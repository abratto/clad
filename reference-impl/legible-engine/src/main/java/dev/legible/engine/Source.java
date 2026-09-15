package dev.legible.engine;

/**
 * A binding source evaluated against a frame to produce zero or more values.
 * Mirrors the paper's {@code where} clause data sources:
 * <ul>
 *   <li>{@link Literal} — a sync constant (Pattern C).</li>
 *   <li>{@link VarRef} — a variable bound earlier in the same sync.</li>
 *   <li>{@link Uuid} — identifier minting ({@code bind(uuid() as ?x)}).</li>
 *   <li>{@link TriggerInput} — a field of the trigger action's input (Pattern A).</li>
 *   <li>{@link TriggerField} — a field of the trigger action's completion (Pattern B).</li>
 *   <li>{@link SiblingInput} — a field of a sibling action's input, in the same flow.</li>
 *   <li>{@link SiblingField} — a field of a sibling action's completion, in the same flow.</li>
 *   <li>{@link StateRead} — a concept-state read (Pattern D).</li>
 *   <li>{@link Subjects} — the inverse-index read: the subjects for which
 *       {@code predicate(subject) = object} (Pattern D inverse). Declarative
 *       and code-free (no filters/aggregation); returns the subject set as a
 *       single collected value. Not the declined {@code frames.query/collectAs}
 *       imperative API — see maintenance/engine-subjects-inverse-read.md.</li>
 *   <li>{@link Collect} — gather the inner source's values into ONE List value
 *       (declarative aggregate; see maintenance/engine-declarative-join-collect.md).</li>
 *   <li>{@link Distinct} — de-duplicate + order the inner source's values into
 *       one List value.</li>
 *   <li>{@link Scan} — every value of a predicate across a concept's region,
 *       as one List value (corpus read).</li>
 *   <li>{@link ConjunctField} — a named conjunct's completion field (join, Pattern B).</li>
 *   <li>{@link ConjunctInput} — a named conjunct's invocation input (join, Pattern A).</li>
 * </ul>
 */
public sealed interface Source permits
        Source.Literal, Source.VarRef, Source.Uuid, Source.TriggerInput,
        Source.TriggerField, Source.SiblingInput, Source.SiblingField, Source.StateRead,
        Source.Subjects, Source.Collect, Source.Distinct, Source.Scan,
        Source.ConjunctField, Source.ConjunctInput {

    record Literal(Object value) implements Source {}

    record VarRef(String var) implements Source {}

    record Uuid() implements Source {}

    record TriggerInput(String field) implements Source {}

    record TriggerField(String field) implements Source {}

    record SiblingInput(String concept, String action, String field) implements Source {}

    record SiblingField(String concept, String action, String field) implements Source {}

    record StateRead(String concept, Source subject, String predicate) implements Source {}

    /** Subjects s where {@code predicate(s) = object}; collected to one List value. */
    record Subjects(String concept, String predicate, Source object) implements Source {}

    /** Gather every value the inner source yields into ONE List value. */
    record Collect(Source inner) implements Source {}

    /** De-duplicate (deterministically ordered) the inner source's values into one List value. */
    record Distinct(Source inner) implements Source {}

    /** Every value of {@code predicate} across {@code concept}'s region, as one List value. */
    record Scan(String concept, String predicate) implements Source {}

    /** A completion field of a named {@code when}-conjunct (joined rule). */
    record ConjunctField(String conjunct, String field) implements Source {}

    /** An invocation input of a named {@code when}-conjunct (joined rule). */
    record ConjunctInput(String conjunct, String field) implements Source {}
}
