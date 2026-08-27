package dev.legible.example.tagging;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;

/** Tags on posts. State: {@code tag(postId) -> tagName} (a set per post). */
public final class TaggingConcept implements Concept {

    private final Region region;

    public TaggingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Tagging";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "tag" -> tag(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    private Map<String, Object> tag(Map<String, Object> input) {
        String postId = (String) input.get("postId");
        String tag = (String) input.get("tag");
        if (postId == null || tag == null) {
            return Map.of("outcome", "error", "message", "missing postId or tag");
        }
        region.write(postId, "tag", tag);
        return Map.of("outcome", "TAGGED", "postId", postId, "tag", tag);
    }
}
