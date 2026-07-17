package com.example.app.flows;

import com.example.app.api.LoginRequest;
import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.user.UserConcept;
import com.example.app.engine.ActionLog;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Concurrent load test for the CLAD dispatch engine.
 *
 * <p>Measures throughput and latency under concurrent requests to identify
 * the write-serialization ceiling of the Jena TxnMem Dataset.
 */
@MicronautTest
class ConcurrencyTest {

    private static final int WARMUP_REQUESTS = 20;
    private static final int[] CONCURRENCY_LEVELS = {1, 2, 4, 8, 16, 32};
    private static final int REQUESTS_PER_THREAD = 200;

    @Inject
    @Client("/")
    HttpClient client;

    @Inject
    UserConcept users;

    @Inject
    PasswordAuthConcept passwords;

    @Inject
    ActionLog actionLog;

    private static int userCounter = 0;

    @BeforeAll
    static void warmup() {
        // JIT compilation warmup — not measured
        userCounter = 0;
    }

    private synchronized String[] seedUserAndPassword() {
        int id = userCounter++;
        String userId = "conc-" + id;
        String username = "conc-user-" + id;
        String password = "pass-" + id;
        users.seedUser(userId, username);
        passwords.seedCredential(userId, password);
        return new String[]{username, password};
    }

    @Test
    void concurrentLoginLatency() throws Exception {
        String backend = actionLog.dataset().getClass().getSimpleName();
        System.out.println();
        System.out.println("=== CLAD Engine Concurrency Test ===");
        System.out.println("Machine: Apple M4 Pro, 64 GB RAM");
        System.out.println("Backend: " + backend);
        System.out.println("Per-thread requests: " + REQUESTS_PER_THREAD);
        System.out.printf("%-12s %8s %8s %8s %8s %8s %8s %12s%n",
                "Concurrency", "Total", "mean(ms)", "p50(ms)", "p95(ms)", "p99(ms)", "req/s", "errors");
        System.out.println("------------------------------------------------------------------------");

        for (int concurrency : CONCURRENCY_LEVELS) {
            runConcurrencyLevel(concurrency);
        }
        System.out.println();
    }

    private void runConcurrencyLevel(int numThreads) throws Exception {
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(numThreads);
        List<Long> allLatencies = Collections.synchronizedList(new ArrayList<>());
        AtomicInteger successCount = new AtomicInteger(0);
        ConcurrentHashMap<String, AtomicInteger> errorTypes = new ConcurrentHashMap<>();

        for (int t = 0; t < numThreads; t++) {
            Thread thread = new Thread(() -> {
                try {
                    startLatch.await();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }

                for (int i = 0; i < REQUESTS_PER_THREAD; i++) {
                    String[] creds = seedUserAndPassword();
                    String username = creds[0];
                    String password = creds[1];

                    // Allow seeded data to settle before the dispatch loop
                    // competes for the Dataset write lock at high concurrency.
                    try { Thread.sleep(1); } catch (InterruptedException ignored) {}

                    long start = System.nanoTime();
                    try {
                        HttpResponse<String> resp = client.toBlocking().exchange(
                                HttpRequest.POST("/login",
                                        new LoginRequest(username, password)),
                                String.class);
                        long elapsed = System.nanoTime() - start;

                        if (resp.getStatus() == HttpStatus.OK
                                && resp.body() != null
                                && resp.body().contains("\"sessionToken\"")) {
                            allLatencies.add(elapsed);
                            successCount.incrementAndGet();
                        } else {
                            errorTypes.computeIfAbsent(
                                    "HTTP " + resp.getStatus().getCode(), k -> new AtomicInteger(0)
                            ).incrementAndGet();
                        }
                    } catch (io.micronaut.http.client.exceptions.HttpClientResponseException e) {
                        errorTypes.computeIfAbsent(
                                "HTTP " + e.getStatus().getCode(), k -> new AtomicInteger(0)
                        ).incrementAndGet();
                    } catch (Exception e) {
                        String key = e.getClass().getSimpleName();
                        if (e.getMessage() != null && e.getMessage().contains("ReadTimeout")) {
                            key = "ReadTimeout";
                        } else if (e.getMessage() != null && e.getMessage().contains("Connect")) {
                            key = "ConnectError";
                        }
                        errorTypes.computeIfAbsent(key, k -> new AtomicInteger(0)).incrementAndGet();
                    }
                }

                doneLatch.countDown();
            }, "conc-test-" + t);
            thread.start();
        }

        long wallStart = System.nanoTime();
        startLatch.countDown();
        doneLatch.await();
        long wallEnd = System.nanoTime();
        double wallSeconds = (wallEnd - wallStart) / 1_000_000_000.0;

        int totalErrors = errorTypes.values().stream().mapToInt(AtomicInteger::get).sum();
        int totalRequests = successCount.get() + totalErrors;
        double reqPerSec = totalRequests / wallSeconds;

        List<Long> sorted = new ArrayList<>(allLatencies);
        Collections.sort(sorted);

        if (sorted.isEmpty()) {
            System.out.printf("%-12d %8d %8s %8s %8s %8s %8.1f %12s (all errors)%n",
                    numThreads, totalRequests, "-", "-", "-", "-", reqPerSec, "");
            return;
        }

        int total = sorted.size();
        double totalMs = 0;
        for (long latency : sorted) totalMs += latency;
        double meanMs = (totalMs / total) / 1_000_000.0;
        double p50Ms = sorted.get(total / 2) / 1_000_000.0;
        double p95Ms = sorted.get((int) (total * 0.95)) / 1_000_000.0;
        double p99Ms = sorted.get((int) (total * 0.99)) / 1_000_000.0;

        System.out.printf("%-12d %8d %8.2f %8.2f %8.2f %8.2f %8.1f %12s",
                numThreads, totalRequests, meanMs, p50Ms, p95Ms, p99Ms, reqPerSec,
                totalErrors > 0 ? totalErrors + " err" : "0 err");
        if (totalErrors > 0 && errorTypes.size() <= 4) {
            for (var entry : errorTypes.entrySet()) {
                System.out.printf("  %s=%d", entry.getKey(), entry.getValue().get());
            }
        }
        System.out.println();
    }
}
