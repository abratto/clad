package dev.legible.example.login;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Concurrency: concurrent flows are isolated by per-flow logs (sharded by flow
 * token), and concept actions are serialized per concept (the state-machine
 * property). These tests would fail without per-concept serialization — the
 * failed-attempt counter would lose updates and lockout would never trigger.
 */
class ConcurrencyTest {

    @Test
    void concurrentLoginsAreCorrectAndIsolated() throws Exception {
        LoginApp app = LoginApp.create();
        app.seedUser("alice", "secret");

        int n = 200;
        ExecutorService pool = Executors.newFixedThreadPool(16);
        CountDownLatch go = new CountDownLatch(1);
        List<Future<Map<String, Object>>> futures = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            futures.add(pool.submit(() -> {
                go.await();
                return app.login("alice", "secret");
            }));
        }
        go.countDown();

        Set<String> tokens = ConcurrentHashMap.newKeySet();
        for (Future<Map<String, Object>> f : futures) {
            Map<String, Object> r = f.get();
            assertEquals(200, r.get("status"));
            assertTrue(r.get("sessionToken") instanceof String);
            tokens.add((String) r.get("sessionToken"));
        }
        pool.shutdown();

        // Every flow got its own fresh session token — no cross-flow contamination.
        assertEquals(n, tokens.size());
    }

    @Test
    void concurrentFailedAttemptsAreNotLost() throws Exception {
        LoginApp app = LoginApp.create();
        app.seedUser("alice", "secret");

        int attempts = 5; // exactly the lockout threshold
        ExecutorService pool = Executors.newFixedThreadPool(8);
        CountDownLatch go = new CountDownLatch(1);
        List<Future<Map<String, Object>>> futures = new ArrayList<>();
        for (int i = 0; i < attempts; i++) {
            futures.add(pool.submit(() -> {
                go.await();
                return app.login("alice", "wrong");
            }));
        }
        go.countDown();

        for (Future<Map<String, Object>> f : futures) {
            assertEquals(401, f.get().get("status"));
        }
        pool.shutdown();

        // Without per-concept serialization the counter would lose updates and
        // fall short of the threshold; here lockout is deterministic.
        Map<String, Object> res = app.login("alice", "secret");
        assertEquals(401, res.get("status"));
        assertEquals("Too many attempts. Try again in 15 minutes.", res.get("message"));
    }
}
