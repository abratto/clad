package com.example.app.infrastructure;

import com.example.app.engine.ActionLog;
import com.example.app.engine.RdfVocabulary;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncMetadata;
import io.micronaut.context.annotation.Requires;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Delete;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.exceptions.HttpStatusException;
import jakarta.inject.Inject;

import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Developer-mode WYSIWID introspection endpoints.
 *
 * <p>These routes expose engine state for local debugging only. They are not
 * part of the business HTTP surface. They require explicit opt-in via
 * {@code prod} environment.
 */
@Controller("/api/dev")
@Requires(notEnv = "prod")
public final class DebugController {

    private static final String NO_SYNC_METADATA = "(no @SyncMetadata)";
    private static final String PREFIX = "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n";
    private static final Pattern CONCEPT_NAME_PATTERN = Pattern.compile("[a-z][a-z0-9]*");

    private final ActionLog actionLog;
    private final List<SyncAgent> syncAgents;

    @Inject
    public DebugController(ActionLog actionLog, List<SyncAgent> syncAgents) {
        this.actionLog = actionLog;
        this.syncAgents = syncAgents;
    }

    @Get(uri = "/flows", produces = MediaType.APPLICATION_JSON)
    public Map<String, List<Map<String, Object>>> flows() {
        return syncAgents.stream()
                .map(this::describeSync)
                .filter(SyncDebugInfo::hasMetadata)
                .sorted(Comparator.comparingInt(SyncDebugInfo::step).thenComparing(SyncDebugInfo::sync))
                .collect(Collectors.groupingBy(
                        SyncDebugInfo::flow,
                        LinkedHashMap::new,
                        Collectors.mapping(SyncDebugInfo::toFlowEntry, Collectors.toList())));
    }

    @Get(uri = "/syncs", produces = MediaType.APPLICATION_JSON)
    public List<Map<String, Object>> syncs() {
        return syncAgents.stream()
                .map(this::describeSync)
                .sorted(Comparator.comparing(SyncDebugInfo::sync))
                .map(SyncDebugInfo::toSyncEntry)
                .toList();
    }

    @Get(uri = "/flow/{token:.*}", produces = MediaType.APPLICATION_JSON)
    public Map<String, Object> flow(String token) {
        String flowToken = requireFlowToken(token);
        List<Map<String, Object>> actions = flowActions(flowToken);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("flowToken", flowToken);
        response.put("actionCount", actions.size());
        response.put("actions", actions);
        if (actions.isEmpty()) {
            response.put("warning", "No actions found in active or archive graphs.");
        }
        return response;
    }

    @Get(uri = "/stuck", produces = MediaType.APPLICATION_JSON)
    public Map<String, Object> stuck() {
        List<Map<String, String>> rows = actionLog.select(
                PREFIX +
                "SELECT ?action ?concept ?name ?flow\n" +
                "WHERE {\n" +
                "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
                "    ?action :concept ?concept ;\n" +
                "            :name ?name ;\n" +
                "            :flow ?flow .\n" +
                "    FILTER NOT EXISTS { << ?action :outcome ?o >> ?p ?v }\n" +
                "  }\n" +
                "}\n" +
                "ORDER BY ?action\n");

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("stuckCount", rows.size());
        response.put("stuck", rows);
        response.put(
                "status",
                rows.isEmpty()
                        ? "No active actions are missing :outcome."
                        : rows.size() + " active action(s) are missing :outcome.");
        return response;
    }

    @Delete(uri = "/actions", produces = MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> clearActions() {
        actionLog.update("DELETE WHERE { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> { ?s ?p ?o } }");
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("graph", RdfVocabulary.ACTION_GRAPH_IRI);
        response.put("status", "Cleared active action graph.");
        return HttpResponse.ok(response);
    }

    @Get(uri = "/concept/{name}/triples", produces = MediaType.APPLICATION_JSON)
    public Map<String, Object> conceptTriples(String name) {
        String conceptName = requireConceptName(name);
        String graph = RdfVocabulary.conceptGraph(conceptName);
        List<Map<String, String>> triples = actionLog.select(
                "SELECT ?subject ?predicate ?object\n" +
                "WHERE {\n" +
                "  GRAPH <" + graph + "> {\n" +
                "    ?subject ?predicate ?object .\n" +
                "  }\n" +
                "}\n" +
                "ORDER BY ?subject ?predicate ?object\n");

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("graph", graph);
        response.put("tripleCount", triples.size());
        response.put("triples", triples);
        return response;
    }

    private List<Map<String, Object>> flowActions(String token) {
        List<Map<String, String>> rows = actionLog.select(
                PREFIX +
                "SELECT ?graph ?action ?concept ?name\n" +
                "WHERE {\n" +
                "  VALUES ?graph { <" + RdfVocabulary.ACTION_GRAPH_IRI + "> <" + RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI + "> }\n" +
                "  GRAPH ?graph {\n" +
                "    ?action :flow <" + token + "> ;\n" +
                "            :concept ?concept ;\n" +
                "            :name ?name .\n" +
                "  }\n" +
                "}\n" +
                "ORDER BY ?graph ?action\n");

        return rows.stream().map(row -> {
            Map<String, Object> action = new LinkedHashMap<>();
            String graph = row.get("graph");
            String actionIri = row.get("action");
            action.put("graph", graph);
            action.put("action", actionIri);
            action.put("concept", row.get("concept"));
            action.put("name", row.get("name"));

            Map<String, String> input = nodeFields(graph, actionIri, "input");
            if (!input.isEmpty()) {
                action.put("input", input);
            }

            Map<String, String> output = nodeFields(graph, actionIri, "output");
            if (!output.isEmpty()) {
                action.put("output", output);
            }
            return action;
        }).toList();
    }

    private static String requireFlowToken(String token) {
        if (token == null || !token.startsWith(RdfVocabulary.FLOW_TOKEN_PREFIX)) {
            throw invalidRequest("flow token must be a CLAD flow IRI");
        }

        String suffix = token.substring(RdfVocabulary.FLOW_TOKEN_PREFIX.length());
        try {
            UUID.fromString(suffix);
            return token;
        } catch (IllegalArgumentException ignored) {
            throw invalidRequest("flow token must be a CLAD flow IRI");
        }
    }

    private static String requireConceptName(String name) {
        if (name != null && CONCEPT_NAME_PATTERN.matcher(name).matches()) {
            return name;
        }
        throw invalidRequest("concept name must be lowercase alphanumeric");
    }

    private static HttpStatusException invalidRequest(String message) {
        return new HttpStatusException(HttpStatus.BAD_REQUEST, message);
    }

    private Map<String, String> nodeFields(String graph, String actionIri, String edge) {
        if ("output".equals(edge)) {
            return outputFields(graph, actionIri);
        }
        List<Map<String, String>> rows = actionLog.select(
                PREFIX +
                "SELECT ?predicate ?value\n" +
                "WHERE {\n" +
                "  GRAPH <" + graph + "> {\n" +
                "    <" + actionIri + "> :" + edge + " ?node .\n" +
                "    ?node ?predicate ?value .\n" +
                "  }\n" +
                "}\n" +
                "ORDER BY ?predicate\n");

        Map<String, String> fields = new LinkedHashMap<>();
        for (Map<String, String> row : rows) {
            fields.put(localName(row.get("predicate")), row.get("value"));
        }
        return fields;
    }

    private Map<String, String> outputFields(String graph, String actionIri) {
        List<Map<String, String>> starRows = actionLog.select(
                PREFIX +
                "SELECT ?_outcome ?predicate ?value\n" +
                "WHERE {\n" +
                "  GRAPH <" + graph + "> {\n" +
                "    << <" + actionIri + "> :outcome ?_outcome >> ?predicate ?value .\n" +
                "  }\n" +
                "}\n" +
                "ORDER BY ?predicate\n");

        Map<String, String> fields = new LinkedHashMap<>();
        if (!starRows.isEmpty()) {
            fields.put("outcome", starRows.get(0).get("_outcome"));
        }
        for (Map<String, String> row : starRows) {
            fields.put(localName(row.get("predicate")), row.get("value"));
        }
        return fields;
    }

    private SyncDebugInfo describeSync(SyncAgent agent) {
        SyncMetadata metadata = metadataOf(agent.getClass());
        if (metadata == null) {
            return SyncDebugInfo.unannotated(agent.syncName());
        }
        return SyncDebugInfo.annotated(
                agent.syncName(),
                metadata.flow(),
                metadata.step(),
                metadata.triggeredBy(),
                metadata.fires(),
                metadata.where());
    }

    private static SyncMetadata metadataOf(Class<?> type) {
        Class<?> current = type;
        while (current != null) {
            SyncMetadata metadata = current.getAnnotation(SyncMetadata.class);
            if (metadata != null) {
                return metadata;
            }
            current = current.getSuperclass();
        }
        return null;
    }

    private static String localName(String iri) {
        return iri != null && iri.startsWith(RdfVocabulary.ACTION_SCHEMA_IRI)
                ? iri.substring(RdfVocabulary.ACTION_SCHEMA_IRI.length())
                : iri;
    }

    private record SyncDebugInfo(
            String sync,
            String flow,
            Integer step,
            String triggeredBy,
            String fires,
            String where) {

        private static SyncDebugInfo unannotated(String sync) {
            return new SyncDebugInfo(sync, null, null, null, null, null);
        }

        private static SyncDebugInfo annotated(
                String sync,
                String flow,
                int step,
                String triggeredBy,
                String fires,
                String where) {
            return new SyncDebugInfo(sync, flow, step, triggeredBy, fires, where);
        }

        private boolean hasMetadata() {
            return step != null;
        }

        private Map<String, Object> toFlowEntry() {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("sync", sync);
            entry.put("step", step);
            entry.put("triggeredBy", triggeredBy);
            entry.put("fires", fires);
            if (where != null && !where.isBlank()) {
                entry.put("where", where);
            }
            return entry;
        }

        private Map<String, Object> toSyncEntry() {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("sync", sync);
            if (!hasMetadata()) {
                entry.put("metadata", NO_SYNC_METADATA);
                return entry;
            }

            Map<String, Object> metadata = new LinkedHashMap<>();
            metadata.put("flow", flow);
            metadata.put("step", step);
            metadata.put("triggeredBy", triggeredBy);
            metadata.put("fires", fires);
            if (where != null && !where.isBlank()) {
                metadata.put("where", where);
            }
            entry.put("metadata", metadata);
            return entry;
        }
    }
}
