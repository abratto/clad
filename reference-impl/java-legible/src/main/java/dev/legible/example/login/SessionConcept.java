package dev.legible.example.login;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Manages bearer-token sessions for a principal. State is the relations
 * {@code userId}, {@code openedAt} over {@code SessionId}.
 */
public final class SessionConcept implements Concept {

    private final Region region;

    public SessionConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Session";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "grant" -> grant(input);
            case "lookup" -> lookup(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    private Map<String, Object> grant(Map<String, Object> input) {
        String userId = (String) input.get("userId");
        if (userId == null) {
            return Map.of("outcome", "error", "message", "missing userId");
        }
        String sessionId = UUID.randomUUID().toString();
        region.write(sessionId, "userId", userId);
        region.write(sessionId, "openedAt", String.valueOf(System.currentTimeMillis()));
        return Map.of("outcome", "GRANTED", "sessionId", sessionId, "userId", userId);
    }

    private Map<String, Object> lookup(Map<String, Object> input) {
        String sessionId = (String) input.get("sessionId");
        if (sessionId == null) {
            return Map.of("outcome", "error", "message", "missing sessionId");
        }
        Set<String> users = region.read(sessionId, "userId");
        if (users.isEmpty()) {
            return Map.of("outcome", "UNKNOWN", "sessionId", sessionId);
        }
        return Map.of("outcome", "ACTIVE", "sessionId", sessionId,
                "userId", users.iterator().next());
    }
}
