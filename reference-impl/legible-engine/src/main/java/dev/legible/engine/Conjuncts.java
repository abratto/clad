package dev.legible.engine;

import java.util.Map;

/**
 * The matched conjuncts of a synchronised (multi-{@code when}) rule: for each
 * named conjunct, the {@link Invocation}/{@link Completion} that satisfied it.
 * Single-trigger rules carry only their one trigger; the empty instance is used
 * when a caller resolves sources outside a join context.
 */
public record Conjuncts(Map<String, Invocation> invocations,
                        Map<String, Completion> completions) {

    public static final Conjuncts EMPTY = new Conjuncts(Map.of(), Map.of());

    public Invocation invocation(String conjunct) {
        return invocations.get(conjunct);
    }

    public Completion completion(String conjunct) {
        return completions.get(conjunct);
    }
}
