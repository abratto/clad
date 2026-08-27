package dev.legible.example.login;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Associates usernames with opaque user identifiers. State is the relation
 * {@code username: UserId -> String} held in this concept's own region.
 */
public final class UserNamingConcept implements Concept {

    private final Region region;

    public UserNamingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "UserNaming";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "register" -> register(input);
            case "lookupByUsername" -> lookup(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    /** Test/seed helper — pre-populate a (userId, username) fact. */
    public void seedUser(String userId, String username) {
        region.write(userId, "username", username);
    }

    private Map<String, Object> register(Map<String, Object> input) {
        String username = (String) input.get("username");
        if (username == null) {
            return Map.of("outcome", "error", "message", "missing username");
        }
        if (!region.subjects("username", username).isEmpty()) {
            return Map.of("outcome", "refused", "message", "username already taken: " + username);
        }
        String userId = UUID.randomUUID().toString();
        region.write(userId, "username", username);
        return Map.of("outcome", "REGISTERED", "userId", userId, "username", username);
    }

    private Map<String, Object> lookup(Map<String, Object> input) {
        String username = (String) input.get("username");
        if (username == null) {
            return Map.of("outcome", "error", "message", "missing username");
        }
        Set<String> subjects = region.subjects("username", username);
        if (subjects.isEmpty()) {
            return Map.of("outcome", "refused", "message", "username not found: " + username);
        }
        String userId = subjects.iterator().next();
        return Map.of("outcome", "FOUND", "userId", userId, "username", username);
    }
}
