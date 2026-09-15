package dev.legible.engine;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * A declarative synchronization rule: {@code when} one or more action
 * completions (a join) occur with given outcomes, {@code where} certain
 * bindings hold, {@code then} invoke further actions. Syncs are pure data — no
 * branching, no state (R3).
 *
 * <p>One rule = one Stage 03 {@code *.sync.md}, mirroring the paper's
 * {@code when}/{@code where}/{@code then} block syntax. A rule with more than
 * one {@link Trigger} is a <em>synchronised</em> (multi-{@code when}) rule: it
 * fires once when every conjunct has a matching completion in the same flow.
 */
public final class SyncRule {

    /** One {@code when} conjunct: a matched action pattern. */
    public record Trigger(String name, String concept, String action, String outcome,
                          Map<String, Object> inputPattern) {
        public Trigger {
            inputPattern = inputPattern == null || inputPattern.isEmpty()
                    ? null : Map.copyOf(inputPattern);
        }

        public Trigger(String name, String concept, String action, String outcome) {
            this(name, concept, action, outcome, null);
        }
    }

    public final String name;
    /** All {@code when} conjuncts (>=1). The first is the primary. */
    public final List<Trigger> triggers;
    public final String triggerConcept;   // primary (triggers[0]), for backwards compatibility
    public final String triggerAction;
    public final String triggerOutcome;   // null = any outcome
    /**
     * Primary trigger's optional input-pattern matcher (R15). Per-conjunct
     * matchers live on each {@link Trigger}.
     */
    public final Map<String, Object> inputPattern;
    public final List<Clause> where;
    public final List<ThenInvocation> then;
    public final String groupBy; // optional ?_eachthen aggregation key

    private SyncRule(String name, List<Trigger> triggers, List<Clause> where,
                     List<ThenInvocation> then, String groupBy) {
        this.name = name;
        this.triggers = List.copyOf(triggers);
        Trigger primary = this.triggers.get(0);
        this.triggerConcept = primary.concept();
        this.triggerAction = primary.action();
        this.triggerOutcome = primary.outcome();
        this.inputPattern = primary.inputPattern();
        this.where = List.copyOf(where);
        this.then = List.copyOf(then);
        this.groupBy = groupBy;
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, List<Clause> where,
                              List<ThenInvocation> then) {
        return of(name, triggerConcept, triggerAction, triggerOutcome, null, where, then, null);
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, List<Clause> where,
                              List<ThenInvocation> then, String groupBy) {
        return of(name, triggerConcept, triggerAction, triggerOutcome, null, where, then, groupBy);
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, Map<String, Object> inputPattern,
                              List<Clause> where, List<ThenInvocation> then) {
        return of(name, triggerConcept, triggerAction, triggerOutcome, inputPattern, where, then, null);
    }

    public static SyncRule of(String name, String triggerConcept, String triggerAction,
                              String triggerOutcome, Map<String, Object> inputPattern,
                              List<Clause> where, List<ThenInvocation> then, String groupBy) {
        return new SyncRule(name,
                List.of(new Trigger("when", triggerConcept, triggerAction, triggerOutcome, inputPattern)),
                where, then, groupBy);
    }

    /** Synchronised (multi-{@code when}) rule: fires once when all triggers matched in one flow. */
    public static SyncRule ofJoin(String name, List<Trigger> triggers, List<Clause> where,
                                  List<ThenInvocation> then, String groupBy) {
        if (triggers == null || triggers.isEmpty()) {
            throw new IllegalArgumentException("a sync requires at least one trigger");
        }
        return new SyncRule(name, new ArrayList<>(triggers), where, then, groupBy);
    }

    /** True when this rule has more than one {@code when} conjunct (a join). */
    public boolean isJoin() {
        return triggers.size() > 1;
    }

    // Convenience constructors for the most common data sources.

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
