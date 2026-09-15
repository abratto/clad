package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Declarative collect/distinct/scan/collectBy (maintenance/
 * engine-declarative-join-collect.md): gather a source's values into one List
 * value, group frames and gather per group, read a whole predicate. Code-free —
 * not the declined frames.query/filter/collectAs imperative API.
 */
class CollectClausesTest {

    private final FactStore facts = new InMemoryFactStore();
    private final ActionLog log = new InMemoryActionLog();
    private final WhereEvaluator ev = new WhereEvaluator(facts, log);

    private static final Invocation INV =
            new Invocation("t1", "f1", null, null, "C", "act", Map.of(), 0L);
    private static final Completion COMP =
            new Completion("t1", "f1", "C", "act", "ok", Map.of(), 0L);

    @Test
    void collectGathersValuesIntoOneListValue() {
        Region tagging = facts.region("Tagging");
        tagging.write("a1", "tags", "java");
        tagging.write("a1", "tags", "rust");

        List<Object> out = ev.resolve(
                Dsl.collect(Dsl.stateRead("Tagging", Dsl.lit("a1"), "tags")),
                Map.of(), INV, COMP);

        assertEquals(1, out.size(), "one List value");
        assertEquals(2, ((List<?>) out.get(0)).size());
    }

    @Test
    void distinctDedupsAndOrders() {
        Region tagging = facts.region("Tagging");
        tagging.write("a1", "tags", "rust");
        tagging.write("a1", "tags", "java");
        tagging.write("a1", "tags", "java"); // duplicate value

        List<Object> out = ev.resolve(
                Dsl.distinct(Dsl.stateRead("Tagging", Dsl.lit("a1"), "tags")),
                Map.of(), INV, COMP);

        assertEquals(List.of("java", "rust"), out.get(0));
    }

    @Test
    void scanReadsEveryValueOfAPredicate() {
        Region tagging = facts.region("Tagging");
        tagging.write("a1", "tags", "java");
        tagging.write("a2", "tags", "go");
        tagging.write("a1", "title", "ignored");

        List<Object> out = ev.resolve(Dsl.scan("Tagging", "tags"), Map.of(), INV, COMP);

        assertEquals(List.of("go", "java"), out.get(0));
    }

    @Test
    void collectByGroupsFramesAndGathersPerGroup() {
        Region catalog = facts.region("Catalog");
        catalog.write("a1", "tagged", "x");
        catalog.write("a2", "tagged", "x");
        Region tagging = facts.region("Tagging");
        tagging.write("a1", "tags", "java");
        tagging.write("a1", "tags", "rust");
        tagging.write("a2", "tags", "go");

        SyncRule rule = SyncRule.of("r", "C", "act", "ok",
                List.of(Dsl.fanOut("?articleId", "Catalog", "tagged", Dsl.lit("x")),
                        Dsl.collectBy("?tags",
                                Dsl.stateRead("Tagging", Dsl.ref("?articleId"), "tags"),
                                "?articleId")),
                List.of());

        List<Map<String, Object>> frames = ev.evaluate(rule, INV, COMP);

        assertEquals(2, frames.size(), "one frame per article");
        assertTrue(frames.stream().anyMatch(f ->
                "a1".equals(f.get("?articleId")) && List.of("java", "rust").equals(f.get("?tags"))));
        assertTrue(frames.stream().anyMatch(f ->
                "a2".equals(f.get("?articleId")) && List.of("go").equals(f.get("?tags"))));
    }
}
