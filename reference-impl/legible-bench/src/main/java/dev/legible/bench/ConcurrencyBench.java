package dev.legible.bench;

import dev.legible.example.login.LoginApp;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Replicates the methodology of the Jena profile's {@code ConcurrencyTest}
 * (reference-impl/java-micronaut-jena/.../flows/ConcurrencyTest.java) against the
 * canonical engine: same concurrency levels, same requests-per-thread, unique
 * user per request, same metrics (mean/p50/p95/p99/req-s/errors).
 */
public final class ConcurrencyBench {

    private static final int WARMUP_REQUESTS = 20;
    private static final int[] CONCURRENCY_LEVELS = {1, 2, 4, 8, 16, 32};
    private static final int REQUESTS_PER_THREAD = 200;

    public static void main(String[] args) throws Exception {
        LoginApp app = LoginApp.create();
        AtomicInteger id = new AtomicInteger();
        for (int i = 0; i < WARMUP_REQUESTS; i++) {
            app.login(seed(app, id), "pass-w");
        }

        System.out.println();
        System.out.println("=== Canonical engine (java-legible) concurrency test ===");
        System.out.println("Per-thread requests: " + REQUESTS_PER_THREAD);
        System.out.printf("%-12s %8s %8s %8s %8s %8s %8s %12s%n",
                "Concurrency", "Total", "mean(ms)", "p50(ms)", "p95(ms)", "p99(ms)", "req/s", "errors");
        System.out.println("------------------------------------------------------------------------");
        for (int concurrency : CONCURRENCY_LEVELS) {
            run(app, concurrency);
        }
        System.out.println();
    }

    private static String seed(LoginApp app, AtomicInteger id) {
        String username = "conc-user-" + id.getAndIncrement();
        app.seedUser(username, "pass-" + username);
        return username;
    }

    private static void run(LoginApp app, int numThreads) throws Exception {
        AtomicInteger id = new AtomicInteger();
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(numThreads);
        List<Long> allLatencies = Collections.synchronizedList(new ArrayList<>());
        AtomicInteger successCount = new AtomicInteger();
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
                    String username = seed(app, id);
                    long start = System.nanoTime();
                    try {
                        Map<String, Object> r = app.login(username, "pass-" + username);
                        if (r != null && Integer.valueOf(200).equals(r.get("status"))) {
                            successCount.incrementAndGet();
                        }
                        allLatencies.add(System.nanoTime() - start);
                    } catch (Exception e) {
                        errorTypes.computeIfAbsent(e.getClass().getSimpleName(), k -> new AtomicInteger()).incrementAndGet();
                    }
                }
                doneLatch.countDown();
            }, "conc-" + t);
            thread.start();
        }

        long wallStart = System.nanoTime();
        startLatch.countDown();
        doneLatch.await();
        long wallEnd = System.nanoTime();
        double wallSeconds = (wallEnd - wallStart) / 1e9;

        int totalErrors = errorTypes.values().stream().mapToInt(AtomicInteger::get).sum();
        int totalRequests = successCount.get() + totalErrors;
        double reqPerSec = totalRequests / wallSeconds;

        List<Long> sorted = new ArrayList<>(allLatencies);
        Collections.sort(sorted);

        if (sorted.isEmpty()) {
            System.out.printf("%-12d %8d %8s %8s %8s %8s %8.1f %12s%n",
                    numThreads, totalRequests, "-", "-", "-", "-", reqPerSec, "all errors");
            return;
        }
        int total = sorted.size();
        double totalMs = 0;
        for (long l : sorted) totalMs += l;
        double meanMs = (totalMs / total) / 1e6;
        double p50 = sorted.get(total / 2) / 1e6;
        double p95 = sorted.get((int) (total * 0.95)) / 1e6;
        double p99 = sorted.get((int) (total * 0.99)) / 1e6;

        System.out.printf("%-12d %8d %8.2f %8.2f %8.2f %8.2f %8.1f %12s%n",
                numThreads, totalRequests, meanMs, p50, p95, p99, reqPerSec,
                totalErrors > 0 ? totalErrors + " err" : "0 err");
    }
}
