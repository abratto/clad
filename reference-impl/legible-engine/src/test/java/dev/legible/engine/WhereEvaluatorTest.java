package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class WhereEvaluatorTest {

    private final FactStore facts = new InMemoryFactStore();
    private final ActionLog log = new InMemoryActionLog();
    private final WhereEvaluator ev = new WhereEvaluator(facts, log);

    private static final Invocation INV =
            new Invocation("t1", "f1", null, null, "C", "act",
                    Map.of("username", "alice", "password", "pw"), 0L);
    private static final Completion COMP =
            new Completion("t1", "f1", "C", "act", "OK", Map.of("userId", "u1"), 0L);

    private List<Map<String, Object>> eval(List<Clause> where) {
        SyncRule rule = SyncRule.of("r", "C", "act", "OK", where, List.of());
        return ev.evaluate(rule, INV, COMP);
    }

    @Test
    void resolvesLiteral() {
        assertEquals(List.of(200), ev.resolve(new Source.Literal(200), Map.of(), INV, COMP));
    }

    @Test
    void resolvesTriggerInput() {
        assertEquals(List.of("alice"),
                ev.resolve(new Source.TriggerInput("username"), Map.of(), INV, COMP));
    }

    @Test
    void resolvesTriggerField() {
        assertEquals(List.of("u1"),
                ev.resolve(new Source.TriggerField("userId"), Map.of(), INV, COMP));
    }

    @Test
    void resolvesMissingFieldAsEmpty() {
        assertEquals(List.of(),
                ev.resolve(new Source.TriggerInput("nope"), Map.of(), INV, COMP));
    }

    @Test
    void resolvesSiblingInputAndField() {
        log.appendInvocation(new Invocation("web1", "f1", null, null, "Web", "request",
                Map.of("password", "pw"), 0L));
        log.appendCompletion(new Completion("web1", "f1", "Web", "request", "routed",
                Map.of("route", "login"), 0L));

        assertEquals(List.of("pw"),
                ev.resolve(new Source.SiblingInput("Web", "request", "password"), Map.of(), INV, COMP));
        assertEquals(List.of("login"),
                ev.resolve(new Source.SiblingField("Web", "request", "route"), Map.of(), INV, COMP));
    }

    @Test
    void resolvesStateReadObject() {
        facts.region("User").write("u1", "email", "a@x.com");
        assertEquals(List.of("a@x.com"),
                ev.resolve(new Source.StateRead("User", new Source.Literal("u1"), "email"),
                        Map.of(), INV, COMP));
    }

    @Test
    void resolvesUuid() {
        List<Object> values = ev.resolve(new Source.Uuid(), Map.of(), INV, COMP);
        assertEquals(1, values.size());
        assertTrue(values.get(0) instanceof String && !((String) values.get(0)).isEmpty());
    }

    @Test
    void bindFromTriggerInput() {
        List<Map<String, Object>> frames = eval(List.of(
                new Clause.Bind("?u", new Source.TriggerInput("username"))));
        assertEquals(1, frames.size());
        assertEquals("alice", frames.get(0).get("?u"));
    }

    @Test
    void bindDropsFrameWhenSourceEmpty() {
        List<Map<String, Object>> frames = eval(List.of(
                new Clause.Bind("?u", new Source.TriggerInput("missing"))));
        assertTrue(frames.isEmpty());
    }

    @Test
    void fanOutEnumeratesSubjects() {
        facts.region("Follow").write("f1", "target", "post1");
        facts.region("Follow").write("f2", "target", "post1");
        facts.region("Follow").write("f3", "target", "post2");

        List<Map<String, Object>> frames = eval(List.of(
                new Clause.FanOut("?f", "Follow", "target", new Source.Literal("post1"))));
        assertEquals(2, frames.size());
        assertTrue(frames.stream().anyMatch(f -> "f1".equals(f.get("?f"))));
        assertTrue(frames.stream().anyMatch(f -> "f2".equals(f.get("?f"))));
    }

    @Test
    void guardKeepsMatchingRouteOnly() {
        log.appendInvocation(new Invocation("web1", "f1", null, null, "Web", "request",
                Map.of("route", "login"), 0L));
        log.appendCompletion(new Completion("web1", "f1", "Web", "request", "routed", Map.of(), 0L));

        List<Map<String, Object>> match = eval(List.of(
                new Clause.Bind("?r", new Source.SiblingInput("Web", "request", "route")),
                new Clause.Guard("?r", new Source.Literal("login"))));
        assertEquals(1, match.size());

        List<Map<String, Object>> noMatch = eval(List.of(
                new Clause.Bind("?r", new Source.SiblingInput("Web", "request", "route")),
                new Clause.Guard("?r", new Source.Literal("register"))));
        assertTrue(noMatch.isEmpty());
    }

    @Test
    void optionalLeavesFrameWhenInnerEmpty() {
        List<Map<String, Object>> frames = eval(List.of(
                new Clause.OptionalClause(
                        new Clause.Bind("?x", new Source.StateRead("Nope", new Source.Literal("s"), "p")))));
        assertEquals(1, frames.size());
        assertEquals(null, frames.get(0).get("?x"));
    }

    @Test
    void groupByDeduplicatesFrames() {
        facts.region("Tag").write("a1", "tag", "t1");
        facts.region("Tag").write("a1", "tag", "t2");

        Invocation inv =
                new Invocation("t1", "f1", null, null, "C", "act", Map.of("article", "a1"), 0L);

        List<Clause> where = List.of(
                new Clause.Bind("?article", new Source.TriggerInput("article")),
                new Clause.Bind("?tag", new Source.StateRead("Tag", new Source.VarRef("?article"), "tag")));

        // without groupBy: two tags on a1 → two frames
        assertEquals(2, ev.evaluate(SyncRule.of("r", "C", "act", "OK", where, List.of()), inv, COMP).size());

        // with groupBy ?article: collapsed to one frame
        List<Map<String, Object>> frames =
                ev.evaluate(SyncRule.of("r", "C", "act", "OK", where, List.of(), "?article"), inv, COMP);
        assertEquals(1, frames.size());
    }
}
