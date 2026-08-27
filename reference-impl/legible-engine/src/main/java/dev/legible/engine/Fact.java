package dev.legible.engine;

/** A fact: {@code predicate(subject) = value} in some concept's region. */
public record Fact(String subject, String predicate, String value) {
}
