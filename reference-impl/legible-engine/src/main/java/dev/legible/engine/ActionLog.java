package dev.legible.engine;

import java.util.List;
import java.util.Optional;
import java.util.Set;

/**
 * The action log: an append-only history of invocations and completions. It is
 * the source of truth for provenance, replay, and sync dedup. A durable
 * implementation persists the same records; the prototype keeps them in memory.
 */
public interface ActionLog {

    void appendInvocation(Invocation inv);

    void appendCompletion(Completion comp);

    Optional<Invocation> invocation(String actionId);

    Optional<Completion> completion(String actionId);

    /** All invocations (for replay / debugging). */
    List<Invocation> invocations();

    /** Invocations in one flow. */
    List<Invocation> invocations(String flowId);

    /**
     * Has a sync already emitted an invocation for a given trigger action? This
     * is the exactly-once dedup marker (replaces the old
     * {@code FILTER NOT EXISTS { ?_when_1 :syncName [] }} SPARQL guard).
     */
    boolean hasEmission(String parentActionId, String syncName);

    /** The completion of {@code (concept, action)} within a flow — for sibling joins. */
    Optional<Completion> completionByFlowAction(String flowId, String concept, String action);

    /** Completions in one flow. */
    List<Completion> completions(String flowId);

    /** All flow ids currently held in the log. */
    Set<String> flowIds();

    /** Remove all records for one flow (archival). */
    void removeFlow(String flowId);

    /** True if any invocation in the flow has no completion yet. */
    default boolean hasPendingInvocations(String flowId) {
        for (Invocation inv : invocations(flowId)) {
            if (completion(inv.actionId()).isEmpty()) return true;
        }
        return false;
    }
}
