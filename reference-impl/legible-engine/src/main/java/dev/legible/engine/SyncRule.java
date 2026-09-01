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
    public final List<Clause> where;
    public final List<ThenInvocation> then;
    public final String groupBy; // optional ?_eachthen aggregation key

    private SyncRule(String name, String triggerConcept, String triggerAction,
                     String triggerOutcome, List<Clause> where,
                     List<ThenInvocation> then, String groupBy) {
        this.name = name;
        this.triggerConcept = triggerConcept;
        this.triggerAction = triggerAction;
        this.triggerOutcome = triggerOutcome;
        this.where = List.copyOf(where);
        this.then = List.copyOf(then);
        this.groupBy = groupBy;
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, List<Clause> where,
                              List<ThenInvocation> then) {
        return new SyncRule(name, triggerConcept, triggerAction, triggerOutcome, where, then, null);
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, List<Clause> where,
                              List<ThenInvocation> then, String groupBy) {
        return new SyncRule(name, triggerConcept, triggerAction, triggerOutcome, where, then, groupBy);
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
