package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static dev.legible.engine.SyncRule.invoke;
import static dev.legible.engine.SyncRule.lit;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Direct coverage of {@link SyncEngine}'s trigger index (the
 * {@code concept/action/outcome} -> rules map that replaced the linear scan).
 * The existing {@code SocialFlowTest} exercises a 3-rule shared bucket
 * end-to-end; these tests drive it with synthetic concepts to pin the exact
 * semantics: bucket grouping, declaration-order preservation, and coexistence
 * of outcome-exact and outcome-agnostic rules on the same trigger.
 */
class SyncTriggerIndexTest {

    /** Records the order actions fired, so tests can assert ordering. */
    private static final class RecordingConcept implements Concept {
        final List<String> log = new ArrayList<>();
        private final String name;

        RecordingConcept(String name) {
            this.name = name;
        }

        @Override
        public String name() {
            return name;
        }

        @Override
        public Map<String, Object> execute(String action, Map<String, Object> input) {
            log.add(action);
            return Map.of("outcome", "OK", "action", action);
        }
    }

    private static final class AnyOutcomeConcept implements Concept {
        @Override
        public String name() {
            return "Root";
        }

        @Override
        public Map<String, Object> execute(String action, Map<String, Object> input) {
            // Mirrors a concept whose outcome is data-dependent; the index must
            // match it correctly regardless of the specific token.
            return Map.of("outcome", input.getOrDefault("outcomeToken", "GEN-A"), "action", action);
        }
    }

    private static FlowRecord lastRecord(SyncEngine engine) {
        return engine.archiver().buffer().latest().orElseThrow();
    }

    private static List<String> firedActionsInOrder(FlowRecord rec, String concept) {
        return rec.invocations().stream()
                .filter(i -> i.concept().equals(concept))
                .map(Invocation::action)
                .collect(java.util.stream.Collectors.toList());
    }

    @Test
    void sharedTriggerFiresEveryMatchingRuleInDeclarationOrder() {
        RecordingConcept sink = new RecordingConcept("Sink");

        // Three rules share the exact trigger Root/start[GO]. Declaration order
        // must survive the index (all three fire, in this order).
        SyncRule a = SyncRule.of("a", "Root", "start", "GO", List.of(),
                List.of(invoke("Sink", "first", Map.of())));
        SyncRule b = SyncRule.of("b", "Root", "start", "GO", List.of(),
                List.of(invoke("Sink", "second", Map.of())));
        SyncRule c = SyncRule.of("c", "Root", "start", "GO", List.of(),
                List.of(invoke("Sink", "third", Map.of())));

        // A deliberately unrelated rule that must NOT fire (different outcome).
        SyncRule ignored = SyncRule.of("i", "Root", "start", "STOP", List.of(),
                List.of(invoke("Sink", "should-not-fire", Map.of())));

        Concept root = new AnyOutcomeConcept();
        SyncEngine engine = new SyncEngine(new InMemoryFactStore(),
                List.of(root, sink), List.of(a, b, c, ignored));

        engine.run("Root", "start", Map.of("outcomeToken", "GO"));

        assertEquals(List.of("first", "second", "third"),
                firedActionsInOrder(lastRecord(engine), "Sink"),
                "all rules in the GO bucket fire, in declaration order");
    }

    @Test
    void outcomeAgnosticRuleFiresForAnyOutcomeAlongsideExactRules() {
        RecordingConcept sink = new RecordingConcept("Sink");

        // triggerOutcome == null: filed under bare `Root/start`, fires for every outcome.
        SyncRule always = SyncRule.of("always", "Root", "start", null, List.of(),
                List.of(invoke("Sink", "always", Map.of())));
        // Outcome-exact: fires only for this one token.
        SyncRule exact = SyncRule.of("exact", "Root", "start", "GO", List.of(),
                List.of(invoke("Sink", "exact", Map.of())));

        Concept root = new AnyOutcomeConcept();
        SyncEngine engine = new SyncEngine(new InMemoryFactStore(),
                List.of(root, sink), List.of(always, exact));

        // GO: both the agnostic and the exact rule fire.
        engine.run("Root", "start", Map.of("outcomeToken", "GO"));
        assertEquals(List.of("exact", "always"),
                firedActionsInOrder(lastRecord(engine), "Sink"));

        // A different outcome: only the agnostic rule fires.
        engine.run("Root", "start", Map.of("outcomeToken", "GEN-B"));
        assertEquals(List.of("always"),
                firedActionsInOrder(lastRecord(engine), "Sink"));
    }

    @Test
    void manyRulesDoNotCollideAcrossConceptsOrOutcomes() {
        RecordingConcept sink = new RecordingConcept("Sink");

        List<SyncRule> rules = new ArrayList<>();
        // 10 rules on Root/start[GO], each emitting a distinct action.
        for (int i = 0; i < 10; i++) {
            rules.add(SyncRule.of("g" + i, "Root", "start", "GO", List.of(),
                    List.of(invoke("Sink", "go-" + i, Map.of()))));
        }
        // 5 rules on a different concept/action — must not fire for Root/start.
        for (int i = 0; i < 5; i++) {
            rules.add(SyncRule.of("x" + i, "Other", "run", "GO", List.of(),
                    List.of(invoke("Sink", "other-" + i, Map.of()))));
        }

        Concept root = new AnyOutcomeConcept();
        SyncEngine engine = new SyncEngine(new InMemoryFactStore(),
                List.of(root, sink), rules);

        engine.run("Root", "start", Map.of("outcomeToken", "GO"));

        List<String> fired = firedActionsInOrder(lastRecord(engine), "Sink");
        assertEquals(10, fired.size(), "only the 10 Root/start[GO] rules fired");
        assertEquals(List.of("go-0", "go-1", "go-2", "go-3", "go-4",
                        "go-5", "go-6", "go-7", "go-8", "go-9"),
                fired, "declaration order is preserved across the bucket");
        assertTrue(fired.stream().noneMatch(a -> a.startsWith("other-")),
                "rules keyed to a different concept/action must not fire");
    }
}
