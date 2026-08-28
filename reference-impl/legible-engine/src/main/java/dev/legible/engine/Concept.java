package dev.legible.engine;

import java.util.Map;

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
}
