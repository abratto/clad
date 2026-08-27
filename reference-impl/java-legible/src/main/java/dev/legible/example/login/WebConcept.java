package dev.legible.example.login;

import dev.legible.engine.Concept;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * The transport bootstrap concept. In the paper's terms this is the
 * "Requesting" concept: {@code request} records the route + parameters (which
 * triggers the first sync), and {@code respond} is the sink every flow ends on.
 *
 * <p>No business logic lives here — only entry/exit. The engine's {@code run}
 * returns the {@code respond} completion's fields, which carry {@code status}
 * plus the response payload.
 */
public final class WebConcept implements Concept {

    @Override
    public String name() {
        return "Web";
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        return switch (action) {
            case "request" -> Map.of("outcome", "routed");
            case "respond" -> {
                Map<String, Object> out = new LinkedHashMap<>();
                out.put("outcome", "sent");
                out.putAll(input);
                yield out;
            }
            default -> Map.of("outcome", "error", "message", "unknown action: " + action);
        };
    }
}
