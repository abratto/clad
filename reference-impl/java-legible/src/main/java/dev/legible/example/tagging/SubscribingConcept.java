package dev.legible.example.tagging;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;

/** Who watches which tag. State: {@code watch(userId) -> tagName} (a set). */
public final class SubscribingConcept implements Concept {

    /** Concept constants for sync rule authoring (see maintenance/sync-dsl-legibility.md). */
    public static final String NAME = "Subscribing";
    public static final String SUBSCRIBE = "subscribe";

    private final Region region;

    public SubscribingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "subscribe" -> subscribe(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    private Map<String, Object> subscribe(Map<String, Object> input) {
        String userId = (String) input.get("userId");
        String tag = (String) input.get("tag");
        if (userId == null || tag == null) {
            return Map.of("outcome", "error", "message", "missing userId or tag");
        }
        region.write(userId, "watch", tag);
        return Map.of("outcome", "SUBSCRIBED", "userId", userId, "tag", tag);
    }
}
