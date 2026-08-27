package dev.legible.example.token;

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
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Coverage for {@code bind(uuid())} in a sync: the token id is minted in the
 * sync's {@code where} clause and handed to a concept that records it.
 */
class TokenFlowTest {

    @Test
    void syncMintsTokenIdAndConceptRecordsIt() {
        TokenApp app = TokenApp.create();

        Map<String, Object> res = app.issue("alice");

        assertEquals(200, res.get("status"));
        String tokenId = (String) res.get("tokenId");
        assertNotNull(tokenId);
        assertFalse(tokenId.isEmpty());
        assertEquals("alice", app.ownerOf(tokenId), "the concept recorded the sync-minted id");
    }

    @Test
    void concurrentIssueMintsUniqueTokens() throws Exception {
        TokenApp app = TokenApp.create();

        int n = 200;
        ExecutorService pool = Executors.newFixedThreadPool(16);
        CountDownLatch go = new CountDownLatch(1);
        List<Future<Map<String, Object>>> futures = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            futures.add(pool.submit(() -> {
                go.await();
                return app.issue("alice");
            }));
        }
        go.countDown();

        Set<String> tokens = ConcurrentHashMap.newKeySet();
        for (Future<Map<String, Object>> f : futures) {
            Map<String, Object> r = f.get();
            assertEquals(200, r.get("status"));
            tokens.add((String) r.get("tokenId"));
        }
        pool.shutdown();

        assertEquals(n, tokens.size(), "every flow must get a distinct sync-minted token id");
    }
}
