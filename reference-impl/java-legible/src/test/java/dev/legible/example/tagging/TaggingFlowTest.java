package dev.legible.example.tagging;

import dev.legible.engine.FlowRecord;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-end coverage for the two matcher constructs the earlier examples never
 * exercised: {@code OPTIONAL} (unbound, not dropped, when a read finds nothing)
 * and {@code ?_eachthen} aggregation (one response per post, not per tag).
 */
class TaggingFlowTest {

    private TaggingApp app;

    @BeforeEach
    void setUp() {
        app = TaggingApp.create();
    }

    @Test
    void optionalBioIsOmittedWhenAbsentAndPresentWhenSet() {
        // No bio yet: the profile still responds (frame survives), bio is null.
        Map<String, Object> absent = app.profile("alice");
        assertEquals(200, absent.get("status"));
        assertEquals("alice", absent.get("userId"));
        assertNull(absent.get("bio"), "bio should be null, not cause the flow to drop");

        // Set a bio, then the profile reads it.
        app.setBio("alice", "hello");
        Map<String, Object> present = app.profile("alice");
        assertEquals(200, present.get("status"));
        assertEquals("hello", present.get("bio"));
    }

    @Test
    void listTagsRespondsOncePerPostRegardlessOfTagCount() {
        String postId = (String) app.publish("alice", "x").get("postId");
        app.tag(postId, "java");
        app.tag(postId, "clad");
        app.tag(postId, "sync");

        Map<String, Object> res = app.listTags(postId);
        assertEquals(200, res.get("status"));
        assertEquals(postId, res.get("postId"));

        // The list flow fanned out to 3 tags but must have produced exactly one
        // response (?_eachthen grouping). Without grouping it would be 3.
        FlowRecord rec = app.engine().archiver().buffer().latest().orElseThrow();
        long responds = rec.invocations().stream()
                .filter(i -> "Web".equals(i.concept()) && "respond".equals(i.action()))
                .count();
        assertEquals(1L, responds, "list-tags should respond once per post, not once per tag");
    }

    @Test
    void tagNotifiesSubscribersViaFanOut() {
        String postId = (String) app.publish("alice", "x").get("postId");
        app.subscribe("carol", "tech");
        app.subscribe("dave", "tech");
        app.subscribe("erin", "gaming");

        app.tag(postId, "tech");

        assertEquals(List.of("New content tagged"), app.notificationsFor("carol"));
        assertEquals(List.of("New content tagged"), app.notificationsFor("dave"));
        assertTrue(app.notificationsFor("erin").isEmpty(), "erin watches gaming, not tech");
        assertFalse(app.notificationsFor("carol").isEmpty());
    }
}
