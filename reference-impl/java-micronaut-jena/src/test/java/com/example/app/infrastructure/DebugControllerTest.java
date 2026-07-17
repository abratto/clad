package com.example.app.infrastructure;

import com.example.app.engine.ActionLog;
import com.example.app.engine.ActionRecord;
import com.example.app.engine.FlowManager;
import com.example.app.engine.RdfVocabulary;
import com.example.app.engine.SyncDispatcher;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.context.annotation.Property;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

@MicronautTest
@Property(name = "clad.debug.endpoints.enabled", value = "true")
class DebugControllerTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Inject
    ActionLog actionLog;

    @Inject
    FlowManager flowManager;

    @Inject
    SyncDispatcher syncDispatcher;

    @Inject
    ObjectMapper objectMapper;

    @BeforeEach
    void resetActionGraphs() {
        actionLog.update("DROP SILENT GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + ">");
        actionLog.update("DROP SILENT GRAPH <" + RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI + ">");
    }

    @Test
    void flows_endpoint_lists_login_sync_metadata() throws Exception {
        Map<String, Object> flows = getMap("/api/dev/flows");

        List<Map<String, Object>> login = asListOfMaps(flows.get("Login"));
        assertEquals(
                List.of(
                    "whenWebHandleRoutedThenUserLookupByUsernameForLogin",
                    "whenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin",
                    "whenUserLookupByUsernameRefusedThenWebRespondForLogin",
                    "whenPasswordAuthCheckBadPasswordThenWebRespondForLogin",
                    "whenPasswordAuthCheckLockedThenWebRespondForLogin",
                    "whenPasswordAuthCheckOkThenSessionGrantForLogin",
                    "whenSessionGrantGrantedThenWebRespondForLogin"),
                login.stream().map(row -> (String) row.get("sync")).toList());
            assertEquals(List.of(1, 2, 2, 3, 3, 3, 4), login.stream()
                .map(row -> ((Number) row.get("step")).intValue())
                .toList());
    }

    @Test
    void flow_endpoint_finds_completed_archived_flow() throws Exception {
        ActionRecord root = flowManager.rootAction("login", Map.of(
                "username", "ada",
                "password", "correct-horse-battery-staple"));

        HttpResponse<?> response = syncDispatcher.awaitResponse(root.flowToken()).block();
        assertEquals(HttpStatus.OK, response.getStatus());

        Map<String, Object> flow = getMap("/api/dev/flow/" + encodePath(root.flowToken()));
        assertEquals(root.flowToken(), flow.get("flowToken"));
        assertTrue(((Number) flow.get("actionCount")).intValue() >= 5);

        List<Map<String, Object>> actions = asListOfMaps(flow.get("actions"));
        assertFalse(actions.isEmpty());
        assertTrue(actions.stream().allMatch(action ->
                RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI.equals(action.get("graph"))));
        assertTrue(actions.stream().anyMatch(action -> "respond".equals(action.get("name"))));
    }

    @Test
    void stuck_endpoint_reports_pending_action_without_output() throws Exception {
        insertPendingAction("pending-check");

        Map<String, Object> stuck = getMap("/api/dev/stuck");
        assertEquals(1, ((Number) stuck.get("stuckCount")).intValue());
        assertTrue(((String) stuck.get("status")).contains("1 active action"));

        List<Map<String, Object>> rows = asListOfMaps(stuck.get("stuck"));
        assertEquals("pending-check", rows.getFirst().get("name"));
    }

    @Test
    void clear_actions_clears_only_active_action_graph() throws Exception {
        ActionRecord root = flowManager.rootAction("login", Map.of(
                "username", "ada",
                "password", "correct-horse-battery-staple"));
        HttpResponse<?> response = syncDispatcher.awaitResponse(root.flowToken()).block();
        assertEquals(HttpStatus.OK, response.getStatus());
        insertPendingAction("pending-delete");

        Map<String, Object> cleared = deleteMap("/api/dev/actions");
        assertEquals(RdfVocabulary.ACTION_GRAPH_IRI, cleared.get("graph"));
        assertEquals("Cleared active action graph.", cleared.get("status"));
        assertEquals(0, countTriples(RdfVocabulary.ACTION_GRAPH_IRI));

        Map<String, Object> stuck = getMap("/api/dev/stuck");
        assertEquals(0, ((Number) stuck.get("stuckCount")).intValue());

        Map<String, Object> archivedFlow = getMap("/api/dev/flow/" + encodePath(root.flowToken()));
        assertTrue(((Number) archivedFlow.get("actionCount")).intValue() >= 5);

        Map<String, Object> conceptTriples = getMap("/api/dev/concept/user/triples");
        assertTrue(((Number) conceptTriples.get("tripleCount")).intValue() > 0);
    }

    @Test
    void flow_endpoint_rejects_non_clad_flow_token() {
        HttpClientResponseException error = assertThrows(
                HttpClientResponseException.class,
                () -> client.toBlocking().retrieve(HttpRequest.GET("/api/dev/flow/not-a-flow-token")));

        assertEquals(HttpStatus.BAD_REQUEST, error.getStatus());
    }

    @Test
    void concept_triples_endpoint_rejects_invalid_concept_name() {
        HttpClientResponseException error = assertThrows(
                HttpClientResponseException.class,
                () -> client.toBlocking().retrieve(HttpRequest.GET("/api/dev/concept/../triples")));

        assertEquals(HttpStatus.BAD_REQUEST, error.getStatus());
    }

    private void insertPendingAction(String name) {
        String action = RdfVocabulary.ACTION_NODE_PREFIX + name;
        String flow = RdfVocabulary.FLOW_TOKEN_PREFIX + name;
        actionLog.update(
                "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
                "INSERT DATA {\n" +
                "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
                "    <" + action + "> :concept <https://clad.dev/concept/debug> ;\n" +
                "                     :name \"" + name + "\" ;\n" +
                "                     :flow <" + flow + "> .\n" +
                "  }\n" +
                "}\n");
    }

    private int countTriples(String graph) {
        List<Map<String, String>> rows = actionLog.select(
                "SELECT (COUNT(*) AS ?count)\n" +
                "WHERE {\n" +
                "  GRAPH <" + graph + "> { ?s ?p ?o }\n" +
                "}\n");
        return Integer.parseInt(rows.getFirst().get("count"));
    }

    private Map<String, Object> getMap(String path) throws Exception {
        String body = client.toBlocking().retrieve(HttpRequest.GET(path));
        return objectMapper.readValue(body, new TypeReference<>() {});
    }

    private Map<String, Object> deleteMap(String path) throws Exception {
        String body = client.toBlocking().retrieve(HttpRequest.DELETE(path));
        return objectMapper.readValue(body, new TypeReference<>() {});
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> asListOfMaps(Object value) {
        return (List<Map<String, Object>>) value;
    }

    private static String encodePath(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
