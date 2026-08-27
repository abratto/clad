package dev.legible.engine;

import java.util.Map;

/**
 * A concept: a singleton state machine holding its own state (via its own
 * {@link Region}) and exposing actions that take and return maps — the paper's
 * "actions are functions over maps". The returned map must contain an
 * {@code "outcome"} key; every other entry is a completion field.
 */
public interface Concept {

    String name();

    Map<String, Object> execute(String action, Map<String, Object> input);
}
