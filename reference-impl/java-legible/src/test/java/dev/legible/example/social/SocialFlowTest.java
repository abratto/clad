package dev.legible.example.social;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-end tests for a feature that is richer than login: fan-out, a Pattern D
 * concept-state read, multiple syncs on one trigger, and a multi-target {@code then}.
 */
class SocialFlowTest {

    private SocialApp app;

    @BeforeEach
    void setUp() {
        app = SocialApp.create();
    }

    @Test
    void publishCreatesPostAndResponds() {
        Map<String, Object> res = app.publish("alice", "hello world");

        assertEquals(200, res.get("status"));
        String postId = (String) res.get("postId");
        assertNotNull(postId);
        assertEquals("alice", app.postAuthor(postId));
    }

    @Test
    void commentNotifiesPostAuthorAndFollowersAndAppendsFeed() {
        String postId = (String) app.publish("alice", "hello world").get("postId");
        app.seedFollow("carol", "bob");
        app.seedFollow("dave", "bob");

        Map<String, Object> res = app.comment(postId, "bob", "nice post");
        assertEquals(200, res.get("status"));
        String commentId = (String) res.get("commentId");
        assertNotNull(commentId);

        // Post author (alice) is notified once — via a Pattern D read of Posting.author.
        assertEquals(List.of("Your post received a comment"), app.notificationsFor("alice"));

        // Both of bob's followers are notified once each — via fan-out over Following.
        assertEquals(List.of("Someone you follow commented"), app.notificationsFor("carol"));
        assertEquals(List.of("Someone you follow commented"), app.notificationsFor("dave"));

        // The commenter is not notified.
        assertTrue(app.notificationsFor("bob").isEmpty());

        // The post author's feed got the comment (second target of the multi-then sync).
        assertEquals(List.of(commentId), app.feedFor("alice"));
    }

    @Test
    void fanOutScalesWithFollowerCount() {
        String postId = (String) app.publish("alice", "hello").get("postId");
        for (int i = 0; i < 7; i++) {
            app.seedFollow("f" + i, "bob");
        }

        app.comment(postId, "bob", "hi");

        for (int i = 0; i < 7; i++) {
            assertEquals(1, app.notificationsFor("f" + i).size(),
                    "follower f" + i + " should be notified exactly once");
        }
        // The post author also got one notification.
        assertEquals(1, app.notificationsFor("alice").size());
    }

    @Test
    void followResponds() {
        Map<String, Object> res = app.follow("bob", "alice");

        assertEquals(200, res.get("status"));
        assertEquals("bob", res.get("followed"));
    }
}
