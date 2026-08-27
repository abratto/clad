package dev.legible.engine;

import java.util.List;
import java.util.Set;

/**
 * One concept's private persistence region (hard rule R2: one named region per
 * concept). A concept holds only its own {@code Region}; a sync's {@code where}
 * clause reads another concept's region through {@link FactStore#region(String)}
 * — the only legal cross-concept read, made visible by name.
 *
 * <p>Facts are relation-shaped: {@code predicate(subject) = value}. The store is
 * storage-agnostic; an in-memory, SQL, or triplestore implementation all expose
 * this same interface.
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
}
