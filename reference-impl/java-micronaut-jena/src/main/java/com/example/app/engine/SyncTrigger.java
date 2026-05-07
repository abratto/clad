package com.example.app.engine;

/**
 * Value object describing the trigger condition for a {@link SyncAgent}.
 *
 * <p>A sync fires when an action completion matching these criteria is observed
 * in the RDF action log:
 * <ul>
 *   <li>{@code conceptIri} — the IRI of the concept that completed the action</li>
 *   <li>{@code actionName} — the name of the completed action</li>
 *   <li>{@code outputStatus} — the output status to match (e.g. "ok" or "error");
 *       {@code null} means "any output"</li>
 * </ul>
 */
public record SyncTrigger(
        String conceptIri,
        String actionName,
        String outputStatus
) {}
