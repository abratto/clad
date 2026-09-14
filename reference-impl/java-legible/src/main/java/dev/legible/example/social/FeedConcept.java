package dev.legible.example.social;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.List;
import java.util.Map;

/** A per-user feed of items. State: {@code item(userId) -> itemId} (a set). */
public final class FeedConcept implements Concept {

    /** Concept constants for sync rule authoring (see maintenance/sync-dsl-legibility.md). */
    public static final String NAME = "Feed";
    public static final String APPEND = "append";

    private final Region region;

    public FeedConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "append" -> append(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    public List<String> itemsFor(String userId) {
        return List.copyOf(region.read(userId, "item"));
    }

    private Map<String, Object> append(Map<String, Object> input) {
        String userId = (String) input.get("userId");
        String itemId = (String) input.get("itemId");
        if (userId == null || itemId == null) {
            return Map.of("outcome", "error", "message", "missing userId or itemId");
        }
        region.write(userId, "item", itemId);
        return Map.of("outcome", "APPENDED", "userId", userId, "itemId", itemId);
    }
}
