package dev.legible.engine;

import dev.legible.example.login.SessionConcept;
import dev.legible.example.login.WebConcept;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static dev.legible.engine.SyncRule.invoke;
import static dev.legible.engine.SyncRule.lit;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

/**
 * Engine-level semantics: fire-after-commit (no rollback), idempotent replay,
 * benign unhandled outcomes, route-scoped syncs on a shared trigger, and
 * bounded-memory archival of completed flows.
 */
class EngineSemanticsTest {

    private static Concept outputConcept(String name, Map<String, Object> output) {
        return new Concept() {
            @Override
            public String name() {
                return name;
            }

            @Override
            public Map<String, Object> execute(String action, Map<String, Object> input) {
                return output;
            }
        };
    }

    private static Concept throwingConcept(String name) {
        return new Concept() {
            @Override
            public String name() {
                return name;
            }

            @Override
            public Map<String, Object> execute(String action, Map<String, Object> input) {
                throw new RuntimeException("boom");
            }
        };
    }

    private static Completion completionOf(FlowRecord rec, String concept, String action) {
        return rec.invocations().stream()
                .filter(i -> i.concept().equals(concept) && i.action().equals(action))
                .findFirst()
                .flatMap(i -> rec.completions().stream()
                        .filter(c -> c.actionId().equals(i.actionId()))
                        .findFirst())
                .orElse(null);
    }

    private static List<FlowRecord> capturingSink() {
        return new ArrayList<>();
    }

    @Test
    void fireAfterCommitLeavesTriggerCompletionIntact() {
        FactStore facts = new InMemoryFactStore();

        Concept a = outputConcept("A", Map.of("outcome", "OK"));
        Concept broken = throwingConcept("Broken");

        SyncRule sync = SyncRule.of(
                "whenADoneThenBrokenFail",
                "A", "do", "OK",
                List.of(),
                List.of(invoke("Broken", "fail", Map.of())));

        List<FlowRecord> captured = capturingSink();
        FlowArchiver archiver = new FlowArchiver(captured::add, new FlowArchiveBuffer(100));
        SyncEngine engine = new SyncEngine(facts, List.of(a, broken), List.of(sync), archiver);
        engine.run("A", "do", Map.of());

        FlowRecord rec = captured.get(0);
        Completion trigger = completionOf(rec, "A", "do");
        assertNotNull(trigger, "trigger completion must be committed (fire-after-commit)");
        assertEquals("OK", trigger.outcome());

        Completion downstream = completionOf(rec, "Broken", "fail");
        assertNotNull(downstream, "the failed downstream action still completes, as an error");
        assertEquals("error", downstream.outcome());
    }

    @Test
    void unhandledOutcomeIsBenign() {
        FactStore facts = new InMemoryFactStore();

        Concept a = outputConcept("A", Map.of("outcome", "STRANGE"));
        List<FlowRecord> captured = capturingSink();
        FlowArchiver archiver = new FlowArchiver(captured::add, new FlowArchiveBuffer(100));
        SyncEngine engine = new SyncEngine(facts, List.of(a), List.of(), archiver);

        // No sync matches STRANGE; the flow simply ends. No exception, no rollback.
        Map<String, Object> res = engine.run("A", "do", Map.of());
        assertNull(res);

        Completion c = completionOf(captured.get(0), "A", "do");
        assertNotNull(c);
        assertEquals("STRANGE", c.outcome());
    }

    @Test
    void replayReprocessesPendingInvocationIdempotently() {
        FactStore facts = new InMemoryFactStore();

        CounterConcept counter = new CounterConcept();
        SyncEngine engine = new SyncEngine(facts, List.of(counter), List.of());

        // Simulate a crash: the invocation was committed to the flow log, but its
        // completion was never written.
        ActionLog flowLog = new InMemoryActionLog();
        flowLog.appendInvocation(new Invocation("c1", "f1", null, null, "Counter", "inc",
                Map.of(), System.currentTimeMillis()));

        engine.drain(flowLog);
        assertEquals(1, counter.count.get());
        assertNotNull(flowLog.completion("c1"));

        // Re-draining (e.g. after a restart) must not double-process.
        engine.drain(flowLog);
        assertEquals(1, counter.count.get());
    }

    @Test
    void archivalBouncesTheBufferAtCapacity() {
        FactStore facts = new InMemoryFactStore();

        Concept a = outputConcept("A", Map.of("outcome", "OK"));
        List<FlowRecord> captured = capturingSink();
        FlowArchiver archiver = new FlowArchiver(captured::add, new FlowArchiveBuffer(2));
        SyncEngine engine = new SyncEngine(facts, List.of(a), List.of(), archiver);

        engine.run("A", "do", Map.of());
        engine.run("A", "do", Map.of());
        engine.run("A", "do", Map.of());

        // The sink saw all three flows.
        assertEquals(3, captured.size());
        // The bounded buffer retained only the two most recent.
        assertEquals(2, archiver.buffer().recent().size());
    }

    @Test
    void routeScopedSyncsOnSharedTrigger() {
        FactStore facts = new InMemoryFactStore();

        Concept web = new WebConcept();
        Concept session = new SessionConcept(facts.region("Session"));

        SyncRule toGrant = SyncRule.of(
                "whenWebRequestThenSessionGrant",
                "Web", "request", "routed",
                List.of(),
                List.of(invoke("Session", "grant", Map.of("userId", lit("u1")))));

        SyncRule loginResponse = respondScoped(200, "login");
        SyncRule registerResponse = respondScoped(201, "register");

        SyncEngine engine = new SyncEngine(facts, List.of(web, session),
                List.of(toGrant, loginResponse, registerResponse));

        assertEquals(200, engine.run("Web", "request", Map.of("route", "login")).get("status"));
        assertEquals(201, engine.run("Web", "request", Map.of("route", "register")).get("status"));
    }

    private static SyncRule respondScoped(int status, String route) {
        return SyncRule.of(
                "whenSessionGrantedThenWebRespondFor" + route,
                "Session", "grant", "GRANTED",
                List.of(
                        new Clause.Bind("?r", new Source.SiblingInput("Web", "request", "route")),
                        new Clause.Guard("?r", lit(route))),
                List.of(invoke("Web", "respond", Map.of("status", lit(status)))));
    }

    private static final class CounterConcept implements Concept {
        final AtomicInteger count = new AtomicInteger();

        @Override
        public String name() {
            return "Counter";
        }

        @Override
        public Map<String, Object> execute(String action, Map<String, Object> input) {
            return Map.of("outcome", "DONE", "count", count.incrementAndGet());
        }
    }
}
