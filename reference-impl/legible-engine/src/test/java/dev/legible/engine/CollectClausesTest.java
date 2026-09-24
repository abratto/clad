package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;

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
        // `collectBy` emits one group per distinct groupKey in FRAME order, and
        // gathers each group's values in source-read order. The source here is
        // `Region.read` (an unordered set), so the WITHIN-group value order is
        // not part of the contract and is deliberately not sorted —
        // frame-order gathering is what keeps parallel `collectBy` clauses
        // positionally aligned (see maintenance/engine-empty-safe-aggregate.md).
        // Assert per-group membership, not order.
        Map<String, Set<Object>> byArticle = new LinkedHashMap<>();
        for (Map<String, Object> f : frames) {
            byArticle.put((String) f.get("?articleId"),
                    new LinkedHashSet<>((List<?>) f.get("?tags")));
        }
        assertEquals(Set.of("java", "rust"), byArticle.get("a1"));
        assertEquals(Set.of("go"), byArticle.get("a2"));
    }

    @Test
    void recordCollectGathersABindingSubsetPerFrame() {
        // A member's open loans, each row carrying { loanId, copy, dueAt }.
        Region lending = facts.region("Lending");
        lending.write("loan1", "borrower", "m1");
        lending.write("loan2", "borrower", "m1");
        lending.write("loan1", "copy", "c1");
        lending.write("loan1", "dueAt", "d1");
        lending.write("loan2", "copy", "c2");
        lending.write("loan2", "dueAt", "d2");

        SyncRule rule = SyncRule.of("r", "C", "act", "ok",
                List.of(Dsl.fanOut("?loanId", "Lending", "borrower", Dsl.lit("m1")),
                        Dsl.bind("?copy", Dsl.stateRead("Lending", Dsl.ref("?loanId"), "copy")),
                        Dsl.bind("?dueAt", Dsl.stateRead("Lending", Dsl.ref("?loanId"), "dueAt")),
                        // All three per-frame vars are collected, so the
                        // non-collected bindings are empty: ONE list.
                        Dsl.collectRecords("?rows", List.of("?loanId", "?copy", "?dueAt"))),
                List.of());

        List<Map<String, Object>> frames = ev.evaluate(rule, INV, COMP);

        assertEquals(1, frames.size(), "one list for the whole frame set");
        List<?> rows = (List<?>) frames.get(0).get("?rows");
        assertEquals(2, rows.size());
        // Assert by identity so the test does not depend on source iteration
        // order — but the copy/dueAt pairing must travel together.
        Map<String, Map<?, ?>> byLoan = new LinkedHashMap<>();
        for (Object row : rows) {
            Map<?, ?> record = (Map<?, ?>) row;
            byLoan.put((String) record.get("?loanId"), record);
        }
        assertEquals("c1", byLoan.get("loan1").get("?copy"));
        assertEquals("d1", byLoan.get("loan1").get("?dueAt"));
        assertEquals("c2", byLoan.get("loan2").get("?copy"));
        assertEquals("d2", byLoan.get("loan2").get("?dueAt"));
    }

    @Test
    void recordCollectGroupsByTheNamedKey() {
        Region lending = facts.region("Lending");
        lending.write("loan1", "loan", "all");
        lending.write("loan2", "loan", "all");
        lending.write("loan3", "loan", "all");
        lending.write("loan1", "group", "g1");
        lending.write("loan2", "group", "g1");
        lending.write("loan3", "group", "g2");

        SyncRule rule = SyncRule.of("r", "C", "act", "ok",
                List.of(Dsl.fanOut("?loanId", "Lending", "loan", Dsl.lit("all")),
                        Dsl.bind("?group", Dsl.stateRead("Lending", Dsl.ref("?loanId"), "group")),
                        Dsl.collectRecordsBy("?rows", List.of("?loanId"), "?group")),
                List.of());

        List<Map<String, Object>> frames = ev.evaluate(rule, INV, COMP);

        assertEquals(2, frames.size(), "one frame per group key");
        Map<String, Set<Object>> byGroup = new LinkedHashMap<>();
        for (Map<String, Object> f : frames) {
            byGroup.put((String) f.get("?group"), new LinkedHashSet<>((List<?>) f.get("?rows")));
        }
        // Each record is the projection of the collected vars, not the raw value.
        Set<Object> g1 = new LinkedHashSet<>();
        g1.add(Map.of("?loanId", "loan1"));
        g1.add(Map.of("?loanId", "loan2"));
        assertEquals(g1, byGroup.get("g1"));
        assertEquals(Set.of(Map.of("?loanId", "loan3")), byGroup.get("g2"));
    }

    @Test
    void recordCollectEmitsEmptyListWhenNoFrameCarriesTheBindings() {
        // No fan-out: the single synthetic frame has none of the collected vars
        // bound, so the group is empty — a zero-item collection is a value.
        SyncRule rule = SyncRule.of("r", "C", "act", "ok",
                List.of(Dsl.collectRecords("?rows", List.of("?copy", "?dueAt"))),
                List.of());

        List<Map<String, Object>> frames = ev.evaluate(rule, INV, COMP);

        assertEquals(1, frames.size());
        assertEquals(List.of(), frames.get(0).get("?rows"));
    }
}
