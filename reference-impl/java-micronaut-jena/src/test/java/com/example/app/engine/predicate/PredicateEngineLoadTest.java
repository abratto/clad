package com.example.app.engine.predicate;

import com.example.app.engine.*;
import org.apache.jena.rdf.model.ResourceFactory;
import org.junit.jupiter.api.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Load test: predicate engine vs reference engine with multi-concept chains.
 *
 * <p>Scenario: 3 concepts in a chain with 3 syncs — each concept processes
 * an action, writes its completion, and the next sync fires.
 *   Origin/generate → Middle/transform → Terminal/collect → respond
 *
 * <p>Measures throughput and latency for both engines under repeated
 * invocations, verifying that the predicate engine's pre-commit
 * evaluation does not degrade performance.
 */
@DisplayName("PredicateEngineLoadTest")
class PredicateEngineLoadTest {

    private static final Logger LOG = LoggerFactory.getLogger(PredicateEngineLoadTest.class);
    private static final int WARMUP = 100;
    private static final int ITERATIONS = 2000;

    @Test
    @DisplayName("reference engine: multi-step chain throughput")
    void referenceEngineThroughput() {
        ActionLog log = new ActionLog();
        CompletionBus bus = new CompletionBus();
        FlowManager flow = new FlowManager(log, bus);

        List<SyncAgent> syncs = createSyncs(log);
        List<ConceptAgent> concepts = createConcepts(log, bus);

        long start = System.nanoTime();
        for (int i = 0; i < ITERATIONS; i++) {
            ActionRecord root = flow.rootAction("test-" + i, Map.of(
                    "value", String.valueOf(i)));
            // Process: Origin → Middle → Terminal
            concepts.get(0).pollAll();
            for (SyncAgent sync : syncs) {
                sync.execute();
            }
            concepts.get(1).pollAll();
            for (SyncAgent sync : syncs) {
                sync.execute();
            }
            concepts.get(2).pollAll();
            for (SyncAgent sync : syncs) {
                sync.execute();
            }
            log.archiveFlow(root.flowToken());
        }
        long elapsed = System.nanoTime() - start;

        double avgMs = (elapsed / 1_000_000.0) / ITERATIONS;
        LOG.info("Reference engine: {} iterations, {:.2f} ms avg, total {} ms",
                ITERATIONS, avgMs, elapsed / 1_000_000.0);
        System.out.printf("  Reference: %,d iterations, %.3f ms avg%n",
                ITERATIONS, avgMs);
    }

    @Test
    @DisplayName("predicate engine: multi-step chain throughput")
    void predicateEngineThroughput() {
        ActionLog log = new ActionLog();
        CompletionBus bus = new CompletionBus();
        FlowManager flow = new FlowManager(log, bus);

        List<SyncAgent> syncs = createSyncs(log);
        PredicateSyncDispatcher dispatcher = new PredicateSyncDispatcher(log, syncs);
        List<ConceptAgent> concepts = createPredicateConcepts(log, bus, dispatcher);

        long start = System.nanoTime();
        for (int i = 0; i < ITERATIONS; i++) {
            ActionRecord root = flow.rootAction("test-" + i, Map.of(
                    "value", String.valueOf(i)));
            // Process: Origin → Middle → Terminal (each evaluates predicates)
            concepts.get(0).pollAll();
            concepts.get(1).pollAll();
            concepts.get(2).pollAll();
            // Syncs fire inside writeCompletion — manual poll is enough
            log.archiveFlow(root.flowToken());
        }
        long elapsed = System.nanoTime() - start;

        double avgMs = (elapsed / 1_000_000.0) / ITERATIONS;
        System.out.printf("  Predicate: %,d iterations, %.3f ms avg%n",
                ITERATIONS, avgMs);
    }

    @Test
    @DisplayName("predicate engine: unmatched outcome is rejected")
    void predicateEngineRejectsUnmatched() {
        ActionLog log = new ActionLog();
        CompletionBus bus = new CompletionBus();

        SyncAgent badSync = new SyncAgent(log) {
            @Override public String syncName() { return "bad"; }
            @Override public SyncTrigger trigger() {
                return new SyncTrigger("https://clad.dev/concept/origin", "generate", "OK");
            }
            @Override protected String whereClause() {
                return " ?_when_1 :concept <https://clad.dev/concept/origin> ; :name \"generate\" . ";
            }
            @Override protected String thenBindings() {
                return " BIND(\"broken!\" AS ?_bad) ";  // will fail
            }
        };

        PredicateSyncDispatcher dispatcher = new PredicateSyncDispatcher(log, List.of(badSync));
        PredicateConceptAgent concept = new TestPredicateConcept(log, bus, dispatcher,
                "https://clad.dev/concept/origin");

        ActionRecord inv = new ActionRecord(
                "https://clad.dev/action/reject-test",
                "https://clad.dev/flow/reject-flow",
                "https://clad.dev/concept/origin",
                "generate",
                Map.of("input", ResourceFactory.createStringLiteral("test")));

        assertThrows(SyncEvaluationException.class,
                () -> concept.writeCompletion(inv, Map.of(
                        "outcome", ResourceFactory.createStringLiteral("OK"))));
    }

    // -- helpers --

    private static List<SyncAgent> createSyncs(ActionLog log) {
        return List.of(
            createSync(log, "originToMiddle",
                    "https://clad.dev/concept/origin", "generate", "OK",
                    "https://clad.dev/concept/middle", "transform"),
            createSync(log, "middleToTerminal",
                    "https://clad.dev/concept/middle", "transform", "DONE",
                    "https://clad.dev/concept/terminal", "collect"),
            createSync(log, "terminalToRespond",
                    "https://clad.dev/concept/terminal", "collect", "GOT",
                    "https://clad.dev/concept/web", "respond")
        );
    }

    private static SyncAgent createSync(ActionLog log, String name,
            String fromConcept, String fromAction, String outcome,
            String toConcept, String toAction) {
        return new SyncAgent(log) {
            @Override public String syncName() { return name; }
            @Override public SyncTrigger trigger() {
                return new SyncTrigger(fromConcept, fromAction, outcome);
            }
            @Override protected String whereClause() {
                return " ?_when_1 :concept <" + fromConcept + "> ; :name \"" + fromAction + "\" . ";
            }
            @Override protected String thenBindings() {
                return " ?_then_1 :concept <" + toConcept + "> ; :name \"" + toAction
                       + "\" ; :input [ :status \"synced\" ] . ";
            }
        };
    }

    private static List<ConceptAgent> createConcepts(ActionLog log, CompletionBus bus) {
        return List.of(
            new RefConcept(log, bus, "https://clad.dev/concept/origin", "generate"),
            new RefConcept(log, bus, "https://clad.dev/concept/middle", "transform"),
            new RefConcept(log, bus, "https://clad.dev/concept/terminal", "collect")
        );
    }

    private static List<ConceptAgent> createPredicateConcepts(
            ActionLog log, CompletionBus bus, PredicateSyncDispatcher dispatcher) {
        return List.of(
            new TestPredicateConcept(log, bus, dispatcher, "https://clad.dev/concept/origin"),
            new TestPredicateConcept(log, bus, dispatcher, "https://clad.dev/concept/middle"),
            new TestPredicateConcept(log, bus, dispatcher, "https://clad.dev/concept/terminal")
        );
    }

    /** Reference engine concept — writes completion without predicate check. */
    private static class RefConcept extends ConceptAgent {
        private final String iri;
        private final String actionName;
        private final boolean isRespond;

        RefConcept(ActionLog log, CompletionBus bus, String iri, String actionName) {
            super(log, bus);
            this.iri = iri;
            this.actionName = actionName;
            this.isRespond = iri.contains("web");
        }
        @Override protected String conceptIRI() { return iri; }
        @Override public void pollAll() { pollAndProcess(actionName); }
        @Override protected void processInvocation(ActionRecord inv) {
            String outcome = isRespond ? "200" : (actionName.equals("generate")
                    ? "OK" : actionName.equals("transform") ? "DONE" : "GOT");
            writeCompletion(inv, Map.of(
                    "outcome", ResourceFactory.createStringLiteral(outcome),
                    "value", ResourceFactory.createStringLiteral(outcome)));
        }
    }

    /** Predicate engine concept — evaluates syncs before writing. */
    private static class TestPredicateConcept extends PredicateConceptAgent {
        private final String iri;
        private final boolean isRespond;

        TestPredicateConcept(ActionLog log, CompletionBus bus,
                             PredicateSyncDispatcher dispatcher, String iri) {
            super(log, bus, dispatcher);
            this.iri = iri;
            this.isRespond = iri.contains("web");
        }
        @Override protected String conceptIRI() { return iri; }
        @Override public void pollAll() { pollAndProcess(isRespond ? "respond" : (
                iri.contains("origin") ? "generate"
                : iri.contains("middle") ? "transform"
                : "collect"));
        }
        @Override protected void processInvocation(ActionRecord inv) {
            String outcome = isRespond ? "200" : (inv.actionName().equals("generate")
                    ? "OK" : inv.actionName().equals("transform") ? "DONE" : "GOT");
            writeCompletion(inv, Map.of(
                    "outcome", ResourceFactory.createStringLiteral(outcome),
                    "value", ResourceFactory.createStringLiteral(outcome)));
        }
    }
}
