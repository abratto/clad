package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Inverse-index read ({@code Source.Subjects}), maintenance/
 * engine-subjects-inverse-read.md: {@code subjects(concept, predicate, object)}
 * collects the subjects s where {@code predicate(s) = object} into ONE List
 * value. Declarative, code-free — not the declined frames.query/collectAs API.
 */
class SubjectsInverseReadTest {

    private final FactStore facts = new InMemoryFactStore();
    private final ActionLog log = new InMemoryActionLog();
    private final WhereEvaluator ev = new WhereEvaluator(facts, log);

    private static final Invocation INV =
            new Invocation("t1", "f1", null, null, "C", "act", Map.of(), 0L);
    private static final Completion COMP =
            new Completion("t1", "f1", "C", "act", "ok", Map.of(), 0L);

    @Test
    void collectsAllSubjectsForAnObjectAsOneListValue() {
        Region tagging = facts.region("Tagging");
        tagging.write("a1", "tags", "javascript");
        tagging.write("a2", "tags", "javascript");
        tagging.write("a3", "tags", "rust");

        List<Object> out = ev.resolve(
                Dsl.subjects("Tagging", "tags", Dsl.lit("javascript")),
                Map.of(), INV, COMP);

        assertEquals(1, out.size(), "collected as one value");
        assertEquals(List.of("a1", "a2"), out.get(0));
    }

    @Test
    void emptyObjectResolvesToNoValue() {
        assertTrue(ev.resolve(
                Dsl.subjects("Tagging", "tags", Dsl.ref("?absent")),
                Map.of(), INV, COMP).isEmpty());
    }

    @Test
    void knownObjectWithNoMatchesYieldsEmptyCollection() {
        List<Object> out = ev.resolve(
                Dsl.subjects("Tagging", "tags", Dsl.lit("nothing")),
                Map.of(), INV, COMP);
        assertEquals(1, out.size());
        assertEquals(List.of(), out.get(0));
    }
}
