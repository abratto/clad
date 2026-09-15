package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Synchronised (multi-{@code when}) rules — the declarative join
 * (maintenance/engine-declarative-join-collect.md): a rule with several
 * conjuncts fires once, when every conjunct has completed in the same flow,
 * independent of completion order.
 */
class JoinEngineTest {

    /** Completes a fixed outcome; records nothing. */
    private static final class DoneConcept implements Concept {
        private final String name;
        private final String outcome;

        DoneConcept(String name, String outcome) {
            this.name = name;
            this.outcome = outcome;
        }

        @Override
        public String name() {
            return name;
        }

        @Override
        public Map<String, Object> execute(String action, Map<String, Object> input) {
            return Map.of("outcome", outcome, "action", action);
        }
    }

    /** Records each invocation's input so the test can inspect the join bindings. */
    private static final class RecordingConcept implements Concept {
        final List<Map<String, Object>> calls = new ArrayList<>();

        @Override
        public String name() {
            return "Sink";
        }

        @Override
        public Map<String, Object> execute(String action, Map<String, Object> input) {
            calls.add(Map.copyOf(input));
            return Map.of("outcome", "OK", "action", action);
        }
    }

    private static SyncRule rootThen(String... targets) {
        Dsl.RuleBuilder b = Dsl.rule("root").when("Root", "start", "GO");
        ThenInvocation[] invocations = new ThenInvocation[targets.length];
        for (int i = 0; i < targets.length; i++) {
            invocations[i] = Dsl.invoke(targets[i], "go", Dsl.args());
        }
        return b.then(invocations).build();
    }

    private static SyncRule joinedRule() {
        return Dsl.rule("join")
                .when(Dsl.conj("a", "A", "go", "DONE"))
                .and(Dsl.conj("b", "B", "go", "DONE"))
                .where(Dsl.bind("?a", Dsl.conjunctField("a", "action")),
                       Dsl.bind("?b", Dsl.conjunctField("b", "action")))
                .then(Dsl.invoke("Sink", "both",
                        Dsl.args("a", Dsl.ref("?a"), "b", Dsl.ref("?b"))))
                .build();
    }

    private RecordingConcept runWith(SyncRule root) {
        RecordingConcept sink = new RecordingConcept();
        List<Concept> concepts = List.of(
                new DoneConcept("Root", "GO"),
                new DoneConcept("A", "DONE"),
                new DoneConcept("B", "DONE"),
                sink);
        SyncEngine engine = new SyncEngine(new InMemoryFactStore(), concepts,
                List.of(root, joinedRule()));
        engine.run("Root", "start", Map.of());
        return sink;
    }

    @Test
    void joinedRuleFiresOnceWhenAllConjunctsComplete() {
        RecordingConcept sink = runWith(rootThen("A", "B"));

        assertEquals(1, sink.calls.size(), "the join must fire exactly once");
        assertEquals("go", sink.calls.get(0).get("a"));
        assertEquals("go", sink.calls.get(0).get("b"));
    }

    @Test
    void joinIsOrderIndependent() {
        // B scheduled before A: the join still fires exactly once.
        RecordingConcept sink = runWith(rootThen("B", "A"));

        assertEquals(1, sink.calls.size(), "order must not matter");
    }

    @Test
    void joinDoesNotFireWhileAConjunctIsMissing() {
        RecordingConcept sink = runWith(rootThen("A")); // B never invoked

        assertTrue(sink.calls.isEmpty(), "an incomplete join must not fire");
    }
}
