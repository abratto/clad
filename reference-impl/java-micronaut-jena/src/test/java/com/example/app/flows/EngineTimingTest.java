package com.example.app.flows;

import com.example.app.api.LoginRequest;
import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.user.UserConcept;
import com.example.app.engine.RdfVocabulary;
import com.example.app.engine.SyncDispatcher;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Capacity / latency baseline for the CLAD dispatch loop.
 *
 * <p>Exercises the full HTTP → engine → response path, measuring
 * end-to-end latency for multiple successful login flows. The dispatch
 * loop's tick-count-per-flow is the dominant latency factor — this test
 * captures that before and after loop refactoring.
 */
@MicronautTest
class EngineTimingTest {

    private static final int ITERATIONS = 50;

    @Inject
    @Client("/")
    HttpClient client;

    @Inject
    UserConcept users;

    @Inject
    PasswordAuthConcept passwords;

    @Test
    void dispatchLoopLatencyBaseline() {
        List<Long> latenciesNs = new ArrayList<>();
        long totalNs = 0;

        for (int i = 0; i < ITERATIONS; i++) {
            String userId = "perf-" + i;
            String username = "perf-user-" + i;
            String password = "pass-" + i;

            users.seedUser(userId, username);
            passwords.seedCredential(userId, password);

            long start = System.nanoTime();
            HttpResponse<String> resp = client.toBlocking().exchange(
                    HttpRequest.POST("/login",
                            new LoginRequest(username, password)),
                    String.class);
            long elapsed = System.nanoTime() - start;

            latenciesNs.add(elapsed);
            totalNs += elapsed;
            assertEquals(HttpStatus.OK, resp.getStatus(),
                    "unexpected status for user " + username);
            assertTrue(resp.body().contains("\"sessionToken\""),
                    "missing sessionToken in response body");
        }

        Collections.sort(latenciesNs);

        double meanMs = (totalNs / (double) ITERATIONS) / 1_000_000.0;
        double p50Ms = latenciesNs.get(latenciesNs.size() / 2) / 1_000_000.0;
        double p95Ms = latenciesNs.get((int) (latenciesNs.size() * 0.95)) / 1_000_000.0;
        double p99Ms = latenciesNs.get((int) (latenciesNs.size() * 0.99)) / 1_000_000.0;
        double minMs = latenciesNs.get(0) / 1_000_000.0;
        double maxMs = latenciesNs.get(latenciesNs.size() - 1) / 1_000_000.0;

        System.out.println();
        System.out.println("=== Dispatch loop latency baseline (" + ITERATIONS + " iterations) ===");
        System.out.printf("  mean : %7.2f ms%n", meanMs);
        System.out.printf("  p50  : %7.2f ms%n", p50Ms);
        System.out.printf("  p95  : %7.2f ms%n", p95Ms);
        System.out.printf("  p99  : %7.2f ms%n", p99Ms);
        System.out.printf("  min  : %7.2f ms%n", minMs);
        System.out.printf("  max  : %7.2f ms%n", maxMs);
        System.out.println();

        // Soft assertion: logins should complete in reasonable time.
        // The dispatch loop currently has ~4 ticks per login
        // (lookup → check → grant → respond) at 50ms/tick, so
        // expect ~200-300ms baseline; fail if wildly above.
        assertTrue(p50Ms < 500, "p50 latency " + p50Ms + "ms exceeds 500ms threshold");
    }

    /**
     * Same baseline but exercising the failure path (refused lookup).
     * Shorter chain — only 2 ticks (lookup → refused → respond).
     */
    @Test
    void refusedLookupLatencyBaseline() {
        List<Long> latenciesNs = new ArrayList<>();

        for (int i = 0; i < ITERATIONS; i++) {
            long start = System.nanoTime();
            int status = 0;
            try {
                client.toBlocking().exchange(
                        HttpRequest.POST("/login",
                                new LoginRequest("no-such-user-" + i, "anything")),
                        String.class);
            } catch (io.micronaut.http.client.exceptions.HttpClientResponseException e) {
                status = e.getStatus().getCode();
            }
            long elapsed = System.nanoTime() - start;

            latenciesNs.add(elapsed);
            assertEquals(401, status, "expected 401 for unknown user");
        }

        Collections.sort(latenciesNs);

        double p50Ms = latenciesNs.get(latenciesNs.size() / 2) / 1_000_000.0;
        double p95Ms = latenciesNs.get((int) (latenciesNs.size() * 0.95)) / 1_000_000.0;
        double minMs = latenciesNs.get(0) / 1_000_000.0;

        System.out.println();
        System.out.println("=== Refused-lookup latency baseline (" + ITERATIONS + " iterations) ===");
        System.out.printf("  p50  : %7.2f ms%n", p50Ms);
        System.out.printf("  p95  : %7.2f ms%n", p95Ms);
        System.out.printf("  min  : %7.2f ms%n", minMs);
        System.out.println();
    }
}
