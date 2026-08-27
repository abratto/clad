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
 * </ul>
 */
public sealed interface Source permits
        Source.Literal, Source.VarRef, Source.Uuid, Source.TriggerInput,
        Source.TriggerField, Source.SiblingInput, Source.SiblingField, Source.StateRead {

    record Literal(Object value) implements Source {}

    record VarRef(String var) implements Source {}

    record Uuid() implements Source {}

    record TriggerInput(String field) implements Source {}

    record TriggerField(String field) implements Source {}

    record SiblingInput(String concept, String action, String field) implements Source {}

    record SiblingField(String concept, String action, String field) implements Source {}

    record StateRead(String concept, Source subject, String predicate) implements Source {}
}
