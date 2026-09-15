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
 *     rule("SessionGrantForLoginWhenPasswordAuthCheckOk")
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

    public static final class RuleBuilder {
        private final String name;
        private String triggerConcept;
        private String triggerAction;
        private String triggerOutcome;
        private Map<String, Object> inputPattern;
        private List<Clause> where = new ArrayList<>();
        private List<ThenInvocation> then = new ArrayList<>();
        private String groupBy;

        private RuleBuilder(String name) {
            this.name = name;
        }

        /** Trigger without a completion token: fires for any outcome. */
        public RuleBuilder when(String concept, String action) {
            this.triggerConcept = concept;
            this.triggerAction = action;
            return this;
        }

        /** Trigger with an outcome token. */
        public RuleBuilder when(String concept, String action, String outcome) {
            this.triggerConcept = concept;
            this.triggerAction = action;
            this.triggerOutcome = outcome;
            return this;
        }

        /** When-clause input matcher (R15, v0.3.6): every key must hold in the trigger input. */
        public RuleBuilder matching(Map<String, Object> pattern) {
            this.inputPattern = pattern;
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
            return SyncRule.of(name, triggerConcept, triggerAction, triggerOutcome,
                    inputPattern, where, then, groupBy);
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
    public static Source subjects(String concept, String predicate, Source object) {
        return new Source.Subjects(concept, predicate, object);
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
    public static Clause bind(String var, Source source) {
        return new Clause.Bind(var, source);
    }

    /** Keep the frame only if {@code frame[var]} equals {@code expected} (route scope, R11/R15). */
    public static Clause guard(String var, Source expected) {
        return new Clause.Guard(var, expected);
    }

    /** Apply {@code inner}; if it yields nothing, keep the original frame ({@code OPTIONAL}). */
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
