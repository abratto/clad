package dev.legible.example.social;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Notifications per user. State: {@code notification(userId) -> message} (a set). */
public final class NotifyingConcept implements Concept {

    private final Region region;

    public NotifyingConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return "Notifying";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "notify" -> notify(input);
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }

    public List<String> notificationsFor(String userId) {
        return List.copyOf(region.read(userId, "notification"));
    }

    private Map<String, Object> notify(Map<String, Object> input) {
        String userId = (String) input.get("userId");
        String message = (String) input.get("message");
        if (userId == null || message == null) {
            return Map.of("outcome", "error", "message", "missing userId or message");
        }
        String notificationId = UUID.randomUUID().toString();
        region.write(userId, "notification", message);
        return Map.of("outcome", "NOTIFIED", "notificationId", notificationId, "userId", userId);
    }
}
