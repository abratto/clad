package dev.legible.engine;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Fluent DSL for declaring {@link SyncRule}s so hand-written rules read
 * like the {@code when → where → then} spec block they realize and remain
 * directly debuggable Java (the SPARQL-era "no gap by readable code"
 * property — see {@code methodology/architecture/SYNC_ENGINE_EVOLUTION.md}).
 *
 * <pre>{&#64;code
 *     import static dev.legible.engine.Dsl.*;
 *
 *     rule("GrantForLoginWhenCheckOk")
 *         .when("PasswordAuth", "check", "OK")
 *         .where(bind("?user", triggerField("userId")))
 *         .then(invoke("Session", "grant", args("userId", ref("?user"))))
 *         .build();
 * }</pre>
 *
 * Every helper returns the same sealed {@link Clause}/{@link Source} records
 * {@code SyncRule.of} would have built — pure sugar, zero behavioural delta.
 * Concept/action names may come from per-feature constants (see
 * {@code maintenance/sync-dsl-legibility.md}).
 */
public final class Dsl {

    private Dsl() {
    }

    // ------------------------------------------------------------------
    // Fluent builder
    // ------------------------------------------------------------------

    public static RuleBuilder rule(String name) {
        return new RuleBuilder(name);
    }

    /** Named {@code when}-conjunct builder (join); may carry its own input matcher (R15). */
    public static final class TriggerSpec {
        private final String name;
        private final String concept;
        private final String action;
        private final String outcome;
        private Map<String, Object> pattern;

        private TriggerSpec(String name, String concept, String action, String outcome) {
            this.name = name;
            this.concept = concept;
            this.action = action;
            this.outcome = outcome;
        }

        /** Per-conjunct input matcher (R15): every key must hold in that conjunct's input. */
        public TriggerSpec matching(Map<String, Object> pattern) {
            this.pattern = pattern;
            return this;
        }

        private SyncRule.Trigger build() {
            return new SyncRule.Trigger(name, concept, action, outcome, pattern);
        }
    }

    /**
     * One named {@code when}-conjunct for a synchronised (multi-{@code when})
     * rule: {@code .when(conj("listed", Catalog, LIST, "Listed")).and(conj(...))}.
     * The first conjunct is the primary trigger.
     */
    public static TriggerSpec conj(String name, String concept, String action, String outcome) {
        return new TriggerSpec(name, concept, action, outcome);
    }

    public static final class RuleBuilder {
        private final String name;
        private final List<SyncRule.Trigger> triggers = new ArrayList<>();
        private List<Clause> where = new ArrayList<>();
        private List<ThenInvocation> then = new ArrayList<>();
        private String groupBy;

        private RuleBuilder(String name) {
            this.name = name;
        }

        /** Trigger without a completion token: fires for any outcome. */
        public RuleBuilder when(String concept, String action) {
            return when(concept, action, null);
        }

        /** Trigger with an outcome token. */
        public RuleBuilder when(String concept, String action, String outcome) {
            triggers.add(new SyncRule.Trigger("when", concept, action, outcome, null));
            return this;
        }

        /** First conjunct of a synchronised rule. */
        public RuleBuilder when(TriggerSpec spec) {
            triggers.add(spec.build());
            return this;
        }

        /** Additional conjunct of a synchronised rule. */
        public RuleBuilder and(TriggerSpec spec) {
            triggers.add(spec.build());
            return this;
        }

        /** When-clause input matcher (R15, v0.3.6): applies to the most recent trigger/conjunct. */
        public RuleBuilder matching(Map<String, Object> pattern) {
            if (triggers.isEmpty()) {
                throw new IllegalStateException("matching() requires a preceding when()/and()");
            }
            int last = triggers.size() - 1;
            SyncRule.Trigger t = triggers.get(last);
            triggers.set(last, new SyncRule.Trigger(t.name(), t.concept(), t.action(), t.outcome(), pattern));
            return this;
        }

        public RuleBuilder where(Clause... clauses) {
            this.where = List.of(clauses);
            return this;
        }

        public RuleBuilder then(ThenInvocation... invocations) {
            this.then = List.of(invocations);
            return this;
        }

        /** {@code ?_eachthen}-style aggregation key (grouped fire, one per key). */
        public RuleBuilder groupBy(String var) {
            this.groupBy = var;
            return this;
        }

        public SyncRule build() {
            return SyncRule.ofJoin(name, triggers, where, then, groupBy);
        }
    }

    // ------------------------------------------------------------------
    // Source factories (kill the `new Source.X(...)` noise)
    // ------------------------------------------------------------------

    /**
     * Absent-input matcher sentinel for `when`-clause input patterns
     * (maintenance/engine-absent-input-matcher.md): a pattern entry with
     * this value requires the matched key to be ABSENT from the trigger
     * input. Complements the R15 value matcher (key present, equal value)
     * with its negation, which invocation-presence gating (partial-update
     * fan-outs) needs. Not a {@code Source} — matcher values only.
     */
    public static final Object ABSENT = new Object() {
        @Override public String toString() { return "absent"; }
    };

    /** Existing convenience: a sync constant. */
    public static Source lit(Object value) {
        return new Source.Literal(value);
    }

    /**
     * Inverse-index read (Pattern D inverse): the subjects for which
     * {@code predicate(subject) = object}, collected into one List value.
     * Dual of {@link #stateRead}; declarative, code-free.
     */
    /** A named conjunct's completion field (join binding, Pattern B). */
    public static Source conjunctField(String conjunct, String field) {
        return new Source.ConjunctField(conjunct, field);
    }

    /** A named conjunct's invocation input (join binding, Pattern A). */
    public static Source conjunctInput(String conjunct, String field) {
        return new Source.ConjunctInput(conjunct, field);
    }

    public static Source subjects(String concept, String predicate, Source object) {
        return new Source.Subjects(concept, predicate, object);
    }

    /**
     * Declarative aggregate: gather every value the inner source yields into
     * ONE List value bound by the enclosing {@code bind}.  The code-free
     * analogue of conceptbox's {@code collectAs} — no filters/JSON.
     */
    public static Source collect(Source inner) {
        return new Source.Collect(inner);
    }

    /** De-duplicated, deterministically ordered copy of the inner source's values (one List value). */
    public static Source distinct(Source inner) {
        return new Source.Distinct(inner);
    }

    /** Every value of {@code predicate} across {@code concept}'s region, as one List value. */
    public static Source scan(String concept, String predicate) {
        return new Source.Scan(concept, predicate);
    }

    /** A previously bound variable. */
    public static Source ref(String var) {
        return new Source.VarRef(var);
    }

    /** {@code bind ( uuid() as ?x )} — identifier minting. */
    public static Source uuid() {
        return new Source.Uuid();
    }

    /** Pattern A: a field of the trigger action's input. */
    public static Source triggerInput(String field) {
        return new Source.TriggerInput(field);
    }

    /** Pattern B: a field of the trigger action's completion. */
    public static Source triggerField(String field) {
        return new Source.TriggerField(field);
    }

    /** A field of a sibling action's input, in the same flow. */
    public static Source siblingInput(String concept, String action, String field) {
        return new Source.SiblingInput(concept, action, field);
    }

    /** A field of a sibling action's completion, in the same flow. */
    public static Source siblingField(String concept, String action, String field) {
        return new Source.SiblingField(concept, action, field);
    }

    /** Pattern D: a concept-state read. */
    public static Source stateRead(String concept, Source subject, String predicate) {
        return new Source.StateRead(concept, subject, predicate);
    }

    // ------------------------------------------------------------------
    // Clause factories
    // ------------------------------------------------------------------

    /** Bind {@code var} from {@code source}; drop the frame if empty. */
    /**
     * Keep the frame only if {@code subject} has no value for {@code predicate}.
     * The negative state pattern (Clause.Absent).
     */
    public static Clause absent(String var, String concept, String predicate) {
        return new Clause.Absent(var, concept, predicate, null);
    }

    /**
     * Keep the frame only if {@code subject} has no value for {@code predicate}
     * equal to {@code object}.
     */
    public static Clause absent(String var, String concept, String predicate, Source object) {
        return new Clause.Absent(var, concept, predicate, object);
    }

    public static Clause bind(String var, Source source) {
        return new Clause.Bind(var, source);
    }

    /** Keep the frame only if {@code frame[var]} equals {@code expected} (route scope, R11/R15). */
    public static Clause guard(String var, Source expected) {
        return new Clause.Guard(var, expected);
    }

    /** Apply {@code inner}; if it yields nothing, keep the original frame ({@code OPTIONAL}). */
    /**
     * Group frames by {@code groupKey} (null = collapse all) and bind {@code var}
     * to the gathered {@code source} values per group — the frame-set analogue
     * of {@link #collect}.
     */
    public static Clause collectBy(String var, Source source, String groupKey) {
        return new Clause.CollectBy(var, source, groupKey);
    }

    /**
     * Record-form collect: gather {@code vars} (a binding subset) from every
     * frame into one record per frame, bound to {@code var} as a List. Frames
     * are grouped by their non-collected bindings. Grouping/projection only —
     * the declarative analogue of conceptbox's {@code collectAs([...], results)}.
     * See {@code maintenance/engine-record-collect.md}.
     */
    public static Clause collectRecords(String var, List<String> vars) {
        return new Clause.RecordCollect(var, List.copyOf(vars), null);
    }

    /** Record-form collect grouped by {@code groupKey} instead of the non-collected bindings. */
    public static Clause collectRecordsBy(String var, List<String> vars, String groupKey) {
        return new Clause.RecordCollect(var, List.copyOf(vars), groupKey);
    }

    public static Clause optional(Clause inner) {
        return new Clause.OptionalClause(inner);
    }

    /** Enumerate subjects of {@code predicate(subject) = object}, fanning out. */
    public static Clause fanOut(String var, String concept, String predicate, Source object) {
        return new Clause.FanOut(var, concept, predicate, object);
    }

    // ------------------------------------------------------------------
    // Then factories
    // ------------------------------------------------------------------

    public static ThenInvocation invoke(String concept, String action, Map<String, Source> args) {
        return new ThenInvocation(concept, action, args);
    }

    /** Argument map builder that tolerates exactly the pairs from {@code args(k1, v1, k2, v2, ...)}. */
    public static Map<String, Source> args(Object... keyValues) {
        if (keyValues.length % 2 != 0) {
            throw new IllegalArgumentException("args() needs key/value pairs");
        }
        Map<String, Source> out = new LinkedHashMap<>();
        for (int i = 0; i < keyValues.length; i += 2) {
            Object k = keyValues[i];
            Object v = keyValues[i + 1];
            if (!(k instanceof String key)) {
                throw new IllegalArgumentException("arg key must be a String: " + k);
            }
            Source source = toSource(v);
            out.put(key, source);
        }
        return out;
    }

    private static Source toSource(Object v) {
        if (v instanceof Source s) return s;
        if (v instanceof String str && str.startsWith("?")) return new Source.VarRef(str);
        return new Source.Literal(v);
    }
}
