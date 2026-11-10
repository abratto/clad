package dev.legible.engine;

import java.util.Map;
import java.util.Set;

/**
 * A concept: a singleton state machine holding its own state (via its own
 * {@link Region}) and exposing actions that take and return maps — the paper's
 * "actions are functions over maps". The returned map must contain an
 * {@code "outcome"} key; every other entry is a completion field.
 *
 * <p><strong>Name the capability, not the entity.</strong> A concept's name is a
 * purpose-oriented noun phrase ({@code Posting}, {@code Authentication},
 * {@code Upvoting}) — never the noun the set ranges over ({@code Post},
 * {@code User}, {@code Comment}). The entity is a separate identifier type that
 * appears in the state relations, not in the concept name. See
 * {@code methodology/architecture/CONCEPTS.md} and Daniel Jackson's
 * <em>Why concepts aren't objects</em>.
 *
 * <p><strong>State over a set, not fields of an object.</strong> State is held
 * as relations {@code predicate(subject) = value} over opaque identifiers, via
 * the concept's own {@link Region} — never as mutable instance fields. This is
 * what keeps an individual free to participate in many concepts, and what keeps
 * a concept from conflating separate concerns into one object.
 */
public interface Concept {

    String name();

    Map<String, Object> execute(String action, Map<String, Object> input);

    /**
     * Whether this concept owns mutable state. Stateless concepts — the
     * transport bootstrap ({@code Web}) and other pure adapters — declare
     * {@code false} so the engine does not take a lock for them. Defaults to
     * {@code true}, preserving the original concept-wide serialization for
     * every existing concept.
     */
    default boolean stateful() {
        return true;
    }

    /**
     * The subject this action mutates, used as the lock key. The engine
     * serializes actions with the same {@code (concept, key)}; different keys
     * may run concurrently. Returning {@code null} (the default) means the
     * action is concept-wide and keeps the original per-concept lock.
     *
     * <p>Only declare a key when the action's read-modify-write is confined to
     * that subject. An action with a cross-subject invariant must stay
     * concept-wide (or override {@link #lockKeys} with every subject it
     * touches).
     */
    default Object lockKey(String action, Map<String, Object> input) {
        return null;
    }

    /**
     * Every subject a multi-subject action mutates. The engine acquires the
     * resulting keys in a deterministic order, so overlapping actions cannot
     * deadlock. Defaults to the single {@link #lockKey}; an empty set keeps the
     * concept-wide lock.
     */
    default Set<Object> lockKeys(String action, Map<String, Object> input) {
        Object key = lockKey(action, input);
        return key == null ? Set.of() : Set.of(key);
    }
}
