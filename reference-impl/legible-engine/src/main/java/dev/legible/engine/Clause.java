package dev.legible.engine;

/**
 * One clause of a sync's declarative {@code where} block. Each clause maps a
 * frame (a set of variable bindings) to zero or more frames, so fan-out is
 * expressed by the clause set rather than by imperative loops (R3).
 */
public sealed interface Clause permits
        Clause.Bind, Clause.FanOut, Clause.Guard, Clause.OptionalClause, Clause.CollectBy {

    /** Bind {@code var} from {@code source}; drop the frame if the source is empty. */
    record Bind(String var, Source source) implements Clause {}

    /** Enumerate subjects of {@code predicate(subject) = object}, fanning out. */
    record FanOut(String var, String concept, String predicate, Source object) implements Clause {}

    /** Keep the frame only if {@code frame[var]} equals {@code expected} (route scope, R11/R15). */
    record Guard(String var, Source expected) implements Clause {}

    /** Apply {@code inner}; if it yields nothing, keep the original frame ({@code OPTIONAL}). */
    record OptionalClause(Clause inner) implements Clause {}

    /**
     * Gather, grouping frames by {@code groupKey} (null = collapse all frames):
     * bind {@code var} to the List of {@code source} values per group. The
     * frame-set analogue of {@link Source.Collect} / conceptbox's {@code collectAs}.
     */
    record CollectBy(String var, Source source, String groupKey) implements Clause {}
}
