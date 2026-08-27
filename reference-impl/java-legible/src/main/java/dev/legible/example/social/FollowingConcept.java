package dev.legible.example.social;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;

/** Who follows whom. State: {@code target(followerId) -> targetId} (a set). */
public final class FollowingConcept implements Concept {

    private final Region region;

    public FollowingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Following";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "follow" -> follow(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    /** Direct seed helper (test fixtures). */
    public void seedFollow(String follower, String target) {
        region.write(follower, "target", target);
    }

    private Map<String, Object> follow(Map<String, Object> input) {
        String follower = (String) input.get("follower");
        String target = (String) input.get("target");
        if (follower == null || target == null) {
            return Map.of("outcome", "error", "message", "missing follower or target");
        }
        region.write(follower, "target", target);
        return Map.of("outcome", "FOLLOWED", "follower", follower, "target", target);
    }
}
