package dev.legible.example.tagging;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;

/**
 * Optional profile data. State: {@code bio(userId) -> text}. The bio may be
 * absent — this is what the {@code OPTIONAL} {@code where} clause reads.
 */
public final class ProfilingConcept implements Concept {

    private final Region region;

    public ProfilingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Profiling";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "setBio" -> setBio(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    private Map<String, Object> setBio(Map<String, Object> input) {
        String userId = (String) input.get("userId");
        String bio = (String) input.get("bio");
        if (userId == null || bio == null) {
            return Map.of("outcome", "error", "message", "missing userId or bio");
        }
        region.write(userId, "bio", bio);
        return Map.of("outcome", "SET", "userId", userId, "bio", bio);
    }
}
