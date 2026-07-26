package com.example.app.engine.predicate;

import com.example.app.engine.*;
import org.apache.jena.rdf.model.ResourceFactory;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the predicate engine.
 *
 * <h3>Paper semantics verified</h3>
 * <ol>
 *   <li>A concept can only commit outcomes with matching sync predicates</li>
 *   <li>Unmatched outcomes throw SyncEvaluationException (pre-commit rejection)</li>
 *   <li>Web/respond bypasses predicate enforcement (terminal action)</li>
 *   <li>Dispatch evaluation returns correct syncs per trigger</li>
 * </ol>
 */
@DisplayName("PredicateEngine")
class PredicateEngineTest {

    private ActionLog log;
    private CompletionBus bus;
    private PredicateSyncDispatcher dispatcher;

    @BeforeEach
    void setUp() {
        log = new ActionLog();
        bus = new CompletionBus();

        SyncAgent testSync = new TestSync(log);
        dispatcher = new PredicateSyncDispatcher(log, List.of(testSync));
    }

    private static class TestConcept extends PredicateConceptAgent {
        TestConcept(ActionLog log, CompletionBus bus, PredicateSyncDispatcher d) {
            super(log, bus, d);
        }
        @Override protected String conceptIRI() { return "https://clad.dev/concept/test"; }
        @Override public void pollAll() {}
        @Override protected void processInvocation(ActionRecord inv) {}
    }

    private static class TestSync extends SyncAgent {
        TestSync(ActionLog log) { super(log); }
        @Override public String syncName() { return "testSync"; }
        @Override public SyncTrigger trigger() {
            return new SyncTrigger("https://clad.dev/concept/test", "doThing", "OK");
        }
        @Override protected String whereClause() {
            return " ?_when_1 :concept <https://clad.dev/concept/test> ; :name \"doThing\" . ";
        }
        @Override protected String thenBindings() {
            return " ?_then_1 :concept <https://clad.dev/concept/test> ; :name \"record\" ; :input [ :status \"synced\" ] . ";
        }
    }

    @Nested
    @DisplayName("Predicate enforcement")
    class PredicateEnforcement {

        @Test
        @DisplayName("matched outcome commits")
        void matchedOutcome() {
            TestConcept concept = new TestConcept(log, bus, dispatcher);
            ActionRecord inv = new ActionRecord(
                    "https://clad.dev/action/test-1",
                    "https://clad.dev/flow/test-flow",
                    "https://clad.dev/concept/test",
                    "doThing",
                    Map.of("input", ResourceFactory.createStringLiteral("test")));

            assertDoesNotThrow(() -> concept.writeCompletion(inv, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("OK"),
                    "result", ResourceFactory.createStringLiteral("done"))));
        }

        @Test
        @DisplayName("unmatched outcome is rejected before state change")
        void unmatchedOutcome() {
            TestConcept concept = new TestConcept(log, bus, dispatcher);
            ActionRecord inv = new ActionRecord(
                    "https://clad.dev/action/test-2",
                    "https://clad.dev/flow/test-flow",
                    "https://clad.dev/concept/test",
                    "doThing",
                    Map.of("input", ResourceFactory.createStringLiteral("test")));

            var ex = assertThrows(SyncEvaluationException.class,
                    () -> concept.writeCompletion(inv, Map.of(
                            "outcome", ResourceFactory.createStringLiteral("UNKNOWN"))));
            assertTrue(ex.getMessage().contains("No sync matches"),
                    "Message should explain no sync matches: " + ex.getMessage());
        }

        @Test
        @DisplayName("Web/respond bypasses predicate enforcement")
        void webRespondBypass() {
            TestConcept concept = new TestConcept(log, bus, dispatcher);
            ActionRecord inv = new ActionRecord(
                    "https://clad.dev/action/web-resp",
                    "https://clad.dev/flow/test-flow",
                    "https://clad.dev/concept/web",
                    "respond",
                    Map.of());

            assertDoesNotThrow(() -> concept.writeCompletion(inv, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("200"),
                    "statusCode", ResourceFactory.createTypedLiteral(200))));
        }
    }

    @Nested
    @DisplayName("Dispatch evaluation")
    class DispatchEvaluation {

        @Test
        @DisplayName("returns matching syncs")
        void returnsMatchingSyncs() {
            List<SyncAgent> matched = dispatcher.evaluateSyncs(
                    "https://clad.dev/concept/test", "doThing", "OK");
            assertEquals(1, matched.size());
            assertEquals("testSync", matched.get(0).syncName());
        }

        @Test
        @DisplayName("returns empty for unmatched outcome")
        void returnsEmptyForUnmatched() {
            List<SyncAgent> matched = dispatcher.evaluateSyncs(
                    "https://clad.dev/concept/test", "doThing", "UNKNOWN");
            assertTrue(matched.isEmpty());
        }

        @Test
        @DisplayName("returns empty for unknown action")
        void returnsEmptyForUnknownAction() {
            List<SyncAgent> matched = dispatcher.evaluateSyncs(
                    "https://clad.dev/concept/test", "noSuchAction", "OK");
            assertTrue(matched.isEmpty());
        }
    }
}
