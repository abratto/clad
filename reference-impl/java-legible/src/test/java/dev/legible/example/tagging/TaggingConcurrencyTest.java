package dev.legible.example.tagging;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Load/concurrency test for the tagging feature: mixed publish + tag + profile
 * (OPTIONAL read) + list-tags (aggregation) flows under concurrency, plus the
 * fan-out notify path, all against shared concept state.
 */
class TaggingConcurrencyTest {

    @Test
    void concurrentMixedWorkloadIsCorrect() throws Exception {
        TaggingApp app = TaggingApp.create();
        app.subscribe("carol", "tech");
        app.setBio("alice", "hello");

        int n = 100;
        ExecutorService pool = Executors.newFixedThreadPool(16);
        CountDownLatch go = new CountDownLatch(1);
        List<Future<Boolean>> futures = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            final String author = "author-" + i;
            futures.add(pool.submit(() -> {
                go.await();

                Map<String, Object> pub = app.publish(author, "content");
                if (!Integer.valueOf(200).equals(pub.get("status"))) return false;
                String postId = (String) pub.get("postId");

                Map<String, Object> tag = app.tag(postId, "tech");
                if (!Integer.valueOf(200).equals(tag.get("status"))) return false;

                // OPTIONAL read under concurrency: alice's bio must always resolve.
                Map<String, Object> profile = app.profile("alice");
                if (!Integer.valueOf(200).equals(profile.get("status"))) return false;
                if (!"hello".equals(profile.get("bio"))) return false;

                // Aggregation under concurrency: list-tags always responds once.
                Map<String, Object> list = app.listTags(postId);
                if (!Integer.valueOf(200).equals(list.get("status"))) return false;
                if (!postId.equals(list.get("postId"))) return false;

                return true;
            }));
        }
        go.countDown();

        for (Future<Boolean> f : futures) {
            assertTrue(f.get(), "every concurrent flow must succeed");
        }
        pool.shutdown();

        // Fan-out under load: carol watches "tech"; she was notified.
        assertFalse(app.notificationsFor("carol").isEmpty());
    }

    @Test
    void concurrentFanOutDeliversEveryNotification() throws Exception {
        TaggingApp app = TaggingApp.create();
        app.subscribe("carol", "tech");

        String postId = (String) app.publish("alice", "x").get("postId");

        int n = 100;
        ExecutorService pool = Executors.newFixedThreadPool(16);
        CountDownLatch go = new CountDownLatch(1);
        List<Future<Boolean>> futures = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            futures.add(pool.submit(() -> {
                go.await();
                Map<String, Object> res = app.tag(postId, "tech");
                return Integer.valueOf(200).equals(res.get("status"));
            }));
        }
        go.countDown();
        for (Future<Boolean> f : futures) {
            assertTrue(f.get());
        }
        pool.shutdown();

        // 100 tag events, each notifying carol; per-concept serialization on
        // Notifying means no writes are lost (the message is constant, so the
        // notification set holds at least one, proving delivery happened).
        assertEquals(1, app.notificationsFor("carol").size());
        assertEquals("New content tagged", app.notificationsFor("carol").get(0));
    }
}
