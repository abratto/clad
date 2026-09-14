package dev.legible.engine;

import java.util.List;
import java.util.Map;

/**
 * A declarative synchronization rule: {@code when} a trigger action completes
 * with a given outcome, {@code where} certain bindings hold, {@code then} invoke
 * further actions. Syncs are pure data — no branching, no state (R3).
 *
 * <p>One rule = one Stage 03 {@code *.sync.md}, mirroring the paper's
 * {@code when}/{@code where}/{@code then} block syntax.
 */
public final class SyncRule {

    public final String name;
    public final String triggerConcept;
    public final String triggerAction;
    public final String triggerOutcome; // null = any outcome
    /**
     * Optional input-pattern matcher on the trigger action's input:
     * every key must be present with an equal value for the rule to fire
     * ({@code when Web/request (route: "profile") : routed}). {@code null}
     * or empty = any input. Pattern matching on trigger inputs mirrors the
     * reference implementation's {@code when X (param: value)} shape and is
     * the preferred way to scope shared triggers by route (R15) — the
     * {@code where}-clause {@code Guard} remains for comparisons a literal
     * when-matcher cannot express.
     */
    public final Map<String, Object> inputPattern;
    public final List<Clause> where;
    public final List<ThenInvocation> then;
    public final String groupBy; // optional ?_eachthen aggregation key

    private SyncRule(String name, String triggerConcept, String triggerAction,
                     String triggerOutcome, Map<String, Object> inputPattern,
                     List<Clause> where,
                     List<ThenInvocation> then, String groupBy) {
        this.name = name;
        this.triggerConcept = triggerConcept;
        this.triggerAction = triggerAction;
        this.triggerOutcome = triggerOutcome;
        this.inputPattern = inputPattern == null || inputPattern.isEmpty()
                ? null : Map.copyOf(inputPattern);
        this.where = List.copyOf(where);
        this.then = List.copyOf(then);
        this.groupBy = groupBy;
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, List<Clause> where,
                              List<ThenInvocation> then) {
        return new SyncRule(name, triggerConcept, triggerAction, triggerOutcome,
                null, where, then, null);
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, List<Clause> where,
                              List<ThenInvocation> then, String groupBy) {
        return new SyncRule(name, triggerConcept, triggerAction, triggerOutcome,
                null, where, then, groupBy);
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, Map<String, Object> inputPattern,
                              List<Clause> where, List<ThenInvocation> then) {
        return new SyncRule(name, triggerConcept, triggerAction, triggerOutcome,
                inputPattern, where, then, null);
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, Map<String, Object> inputPattern,
                              List<Clause> where, List<ThenInvocation> then, String groupBy) {
        return new SyncRule(name, triggerConcept, triggerAction, triggerOutcome,
                inputPattern, where, then, groupBy);
    }

    // Convenience constructors for the most common data sources, so sync
    // declarations read close to the spec's `when`/`where`/`then` syntax.

    public static Source lit(Object value) {
        return new Source.Literal(value);
    }

    public static Source ref(String var) {
        return new Source.VarRef(var);
    }

    public static ThenInvocation invoke(String concept, String action, Map<String, Source> args) {
        return new ThenInvocation(concept, action, args);
    }
}
