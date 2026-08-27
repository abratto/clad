package dev.legible.engine;

import java.util.Map;

/**
 * An action invocation — the "request" half of the paper's invocation/completion
 * split. Committed to the log before the concept runs. {@code parentActionId} and
 * {@code causedBySync} are the provenance edges that link every action back to the
 * sync whose {@code then} clause emitted it.
 */
public record Invocation(
        String actionId,
        String flowId,
        String parentActionId,
        String causedBySync,
        String concept,
        String action,
        Map<String, Object> input,
        long invokedAt) {
}
