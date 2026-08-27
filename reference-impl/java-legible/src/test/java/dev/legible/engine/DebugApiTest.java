package dev.legible.engine;

import dev.legible.example.login.LoginApp;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The debug/introspection surface: query the action log by flow id (in-flight
 * log and archive-buffer fallback), report stuck (pending) invocations, dump a
 * concept's state, and list registered syncs — all without SPARQL.
 */
class DebugApiTest {

    @Test
    void flowLookupByArchivedFlowId() {
        LoginApp app = LoginApp.create();
        app.seedUser("alice", "secret");
        assertEquals(200, app.login("alice", "secret").get("status"));

        // After run() the flow is archived; the debug surface finds it via the buffer.
        String flowId = app.engine().archiver().buffer().latest().orElseThrow().flowId();
        DebugApi debug = app.engine().debug();

        Map<String, Object> flow = debug.flow(flowId);
        assertEquals("archive-buffer", flow.get("source"));
        assertEquals(5, flow.get("actionCount")); // request, lookup, check, grant, respond

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> actions = (List<Map<String, Object>>) flow.get("actions");
        assertEquals("Web", actions.get(0).get("concept"));
        assertEquals("request", actions.get(0).get("action"));
        assertEquals("Web", actions.get(4).get("concept"));
        assertEquals("respond", actions.get(4).get("action"));
        assertEquals(200, ((Map<?, ?>) actions.get(4).get("fields")).get("status"));
        assertEquals("WhenSessionGrantGrantedThenWebRespondForLogin",
                actions.get(4).get("causedBySync"));
    }

    @Test
    void flowLookupInActiveLog() {
        FactStore facts = new InMemoryFactStore();
        ActionLog flowLog = new InMemoryActionLog();
        flowLog.appendInvocation(new Invocation("a1", "f9", null, null, "C", "act", Map.of("x", "1"), 10L));
        flowLog.appendCompletion(new Completion("a1", "f9", "C", "act", "OK", Map.of("y", "2"), 20L));

        Map<String, ActionLog> inFlight = new ConcurrentHashMap<>();
        inFlight.put("f9", flowLog);
        DebugApi debug = new DebugApi(inFlight, facts, List.of(), new FlowArchiveBuffer(0));

        Map<String, Object> flow = debug.flow("f9");
        assertEquals("active-log", flow.get("source"));
        assertEquals(1, flow.get("actionCount"));
    }

    @Test
    void stuckReportsPendingInvocations() {
        FactStore facts = new InMemoryFactStore();
        ActionLog flowLog = new InMemoryActionLog();
        flowLog.appendInvocation(new Invocation("p1", "f1", null, null, "C", "act", Map.of(), 0L));

        Map<String, ActionLog> inFlight = new ConcurrentHashMap<>();
        inFlight.put("f1", flowLog);
        DebugApi debug = new DebugApi(inFlight, facts, List.of(), new FlowArchiveBuffer(0));

        assertEquals(1, debug.stuck().get("stuckCount"));
    }

    @Test
    void conceptDumpsStateFacts() {
        LoginApp app = LoginApp.create();
        app.seedUser("alice", "secret");

        Map<String, Object> user = app.engine().debug().concept("UserNaming");
        assertTrue(((Number) user.get("factCount")).intValue() >= 1);

        @SuppressWarnings("unchecked")
        List<Map<String, String>> facts = (List<Map<String, String>>) user.get("facts");
        assertTrue(facts.stream().anyMatch(f ->
                "username".equals(f.get("predicate")) && "alice".equals(f.get("value"))));
    }

    @Test
    void syncsListsRegisteredRules() {
        LoginApp app = LoginApp.create();
        assertEquals(7, app.engine().debug().syncs().size());
    }
}
