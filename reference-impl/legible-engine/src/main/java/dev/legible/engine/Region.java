package dev.legible.engine;

import java.util.List;
import java.util.Set;

/**
 * One concept's private persistence region (hard rule R2: one named region per
 * concept). A concept holds only its own {@code Region}; a sync's {@code where}
 * clause reads another concept's region through {@link FactStore#region(String)}
 * — the only legal cross-concept read, made visible by name.
 *
 * <p>Facts are relation-shaped: {@code predicate(subject) = value}. This is the
 * relational view — state over a set of opaque individuals, never mutable fields
 * of an object (Daniel Jackson, <em>Why concepts aren't objects</em>). The store
 * is storage-agnostic; an in-memory, SQL, or triplestore implementation all
 * expose this same interface.
 *
 * <p><strong>Composite subjects.</strong> An objectified fact type such as
 * {@code (FirmUri, Service) -> Jurisdiction} has a composite reference scheme:
 * the individual <em>is</em> the pair. Such an individual is addressed with the
 * list-subject overloads below ({@code write(List.of(firm, service), ...)}); a
 * relational realisation keys it on the component columns directly, with no
 * surrogate identifier and no mapping table. Concepts whose individuals are
 * single-valued keep using the plain {@code String} forms, which delegate to the
 * list forms.
 */
public interface Region {

    /** Values of {@code predicate(subject)}. */
    Set<String> read(String subject, String predicate);

    /** Assert {@code predicate(subject) = value}. */
    void write(String subject, String predicate, String value);

    /** Retract one {@code predicate(subject) = value} fact. */
    void remove(String subject, String predicate, String value);

    /** Retract all values of {@code predicate(subject)}. */
    void clear(String subject, String predicate);

    /** Subjects for which {@code predicate(subject) = value} holds (fan-out). */
    Set<String> subjects(String predicate, String value);

    /** All facts in this region (debug/introspection). */
    List<Fact> facts();

    // ---- composite-subject forms --------------------------------------------

    /**
     * Values of {@code predicate(subject)} where the individual is a composite
     * key (its parts). Returns the values (not the subject parts).
     */
    default Set<String> read(List<String> subject, String predicate) {
        return read(join(subject), predicate);
    }

    /** Assert {@code predicate(subject) = value} for a composite individual. */
    default void write(List<String> subject, String predicate, String value) {
        write(join(subject), predicate, value);
    }

    /** Retract one composite-individual fact. */
    default void remove(List<String> subject, String predicate, String value) {
        remove(join(subject), predicate, value);
    }

    /** Retract all values of {@code predicate} for a composite individual. */
    default void clear(List<String> subject, String predicate) {
        clear(join(subject), predicate);
    }

    /** Default join used only by backends that do not model composite keys. */
    static String join(List<String> parts) {
        return String.join("\u0000", parts);
    }

    // ---- member-qualified forms ---------------------------------------------

    /**
     * Values of {@code predicate(subject)}, where the individual is addressed
     * as {@code member} — a subtype/partition member of the concept's state
     * model (e.g. {@code Client} or {@code Supplier} where {@code Client is a
     * Party}).
     *
     * <p><strong>Semantics.</strong> Conceptually a concept region is ONE
     * region; members are a relational-realization dimension (how a durable
     * backend physically splits a partitioned or separated supertype's
     * state). Backends that do not model members — the in-memory store, the
     * generic fact relation — ignore the qualifier, which is exactly their
     * correct behavior. A backend that realises subtypes as separate tables
     * (the Rmap {@code separate}/{@code partition} mappings) routes the
     * operation to the member's own table; for a partitioned supertype this
     * is the only way a shared (flattened) predicate is unambiguous.
     */
    default Set<String> read(String member, String subject, String predicate) {
        return read(subject, predicate);
    }

    /** Assert {@code predicate(subject) = value} for a member individual. */
    default void write(String member, String subject, String predicate, String value) {
        write(subject, predicate, value);
    }

    /** Retract one fact of a member individual. */
    default void remove(String member, String subject, String predicate, String value) {
        remove(subject, predicate, value);
    }

    /** Retract all values of {@code predicate} for a member individual. */
    default void clear(String member, String subject, String predicate) {
        clear(subject, predicate);
    }
}
