package dev.legible.engine;

import java.util.Map;

/**
 * A {@code then} invocation: invoke {@code (concept, action)} with arguments
 * resolved per frame from the {@code where} bindings or constants.
 */
public record ThenInvocation(String concept, String action, Map<String, Source> args) {
}
