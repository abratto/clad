package dev.legible.engine;

import java.util.Map;

/**
 * An action completion — the "result" half. Written after the concept's action
 * has run. {@code outcome} is a first-class named result (e.g. {@code OK},
 * {@code FOUND}, {@code BAD_PASSWORD}, {@code error}), never an exception to
 * roll back.
 */
public record Completion(
        String actionId,
        String flowId,
        String concept,
        String action,
        String outcome,
        Map<String, Object> fields,
        long completedAt) {
}
