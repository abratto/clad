package com.example.app.engine;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Drives concept agents and sync agents on a polling loop until a
 * {@code Web/respond} completion for a given flow token is observed, then
 * delivers the HTTP response.
 *
 * <p>This is the only scheduler in the system. There is no Java event bus —
 * all coordination happens through reading and writing RDF triples in the
 * Jena Dataset (WYSIWID Rule 4).
 *
 * <p>The engine only reads response status and fields from the action graph.
 * Response body serialization to JSON is handled by Micronaut's Jackson
 * serializer at the HTTP boundary — not by string concatenation in the
 * engine. See {@code ResponseAssembler} for typed DTO construction.
 */
@Singleton
public class SyncDispatcher {

    public static final String FLOW_TOKEN_HEADER = "X-Flow-Token";

    private static final String SCHEMA = RdfVocabulary.ACTION_SCHEMA_IRI;
    private static final Duration POLL_INTERVAL = Duration.ofMillis(50);

    private final Duration timeout;
    private static final Duration DEFAULT_TIMEOUT = Duration.ofSeconds(5);
    private static final String STATUS_CODE = "statusCode";
    private static final String TIMEOUT_MESSAGE = "Request timed out";

    /** Max wall-clock time before returning a failure response.
     *  Override with {@code clad.dispatch.timeout.seconds} system property. */
    private static Duration resolveTimeout() {
        String val = System.getProperty("clad.dispatch.timeout.seconds");
        if (val != null) {
            try { return Duration.ofSeconds(Long.parseLong(val)); }
            catch (NumberFormatException ignored) {}
        }
        return DEFAULT_TIMEOUT;
    }

    private final ActionLog actionLog;
    private final List<ConceptAgent> conceptAgents;
    private final CompletionBus completionBus;
    private final Map<String, List<SyncAgent>> triggerIndex;
    private final Map<String, List<ConceptAgent>> pendingInvocationIndex;
    private final Set<String> pendingConcepts = ConcurrentHashMap.newKeySet();

    @Inject
    public SyncDispatcher(
            ActionLog actionLog,
            List<ConceptAgent> conceptAgents,
            List<SyncAgent> syncAgents,
            CompletionBus completionBus) {
        this.actionLog = actionLog;
        this.conceptAgents = conceptAgents;
        this.completionBus = completionBus;
        this.timeout = resolveTimeout();
        this.triggerIndex = buildTriggerIndex(syncAgents);
        this.pendingInvocationIndex = buildPendingInvocationIndex(syncAgents, conceptAgents);
    }

    private static Map<String, List<SyncAgent>> buildTriggerIndex(List<SyncAgent> agents) {
        Map<String, List<SyncAgent>> index = new LinkedHashMap<>();
        for (SyncAgent agent : agents) {
            index.computeIfAbsent(agent.trigger().conceptIri(), k -> new ArrayList<>()).add(agent);
        }
        return index;
    }

    private static Map<String, List<ConceptAgent>> buildPendingInvocationIndex(
            List<SyncAgent> syncAgents, List<ConceptAgent> conceptAgents) {
        Map<String, List<ConceptAgent>> byIri = new LinkedHashMap<>();
        for (ConceptAgent ca : conceptAgents) {
            byIri.computeIfAbsent(ca.conceptIRI(), k -> new ArrayList<>()).add(ca);
        }
        Map<String, List<ConceptAgent>> index = new LinkedHashMap<>();
        for (SyncAgent sa : syncAgents) {
            String targetIri = sa.targetConceptIri();
            if (targetIri == null) continue;
            List<ConceptAgent> targets = byIri.get(targetIri);
            if (targets != null) {
                index.computeIfAbsent(targetIri, k -> new ArrayList<>()).addAll(targets);
            }
        }
        for (Map.Entry<String, List<ConceptAgent>> e : index.entrySet()) {
            e.setValue(e.getValue().stream().distinct().toList());
        }
        return index;
    }

    /**
     * Awaits a {@code Web/respond} completion for the given flow token, driving
     * the dispatch loop until the response is available or {@value #TIMEOUT}
     * is exceeded.
     *
     * <p>Within each tick the loop iterates concepts→syncs until quiescence
     * (no more syncs fire), processing the full action chain for the current
     * flow in a single tick rather than spreading it across multiple ticks.
     * This eliminates the race window where a sync's downstream invocation
     * would wait for the next tick boundary before being polled.
     */
    public Mono<io.micronaut.http.HttpResponse<?>> awaitResponse(String flowToken) {
        return Mono.<io.micronaut.http.HttpResponse<?>>create(sink -> {
            long deadline = System.currentTimeMillis() + timeout.toMillis();
            while (System.currentTimeMillis() < deadline) {
                try {
                    runTick();

                    Optional<io.micronaut.http.HttpResponse<?>> resp = buildResponse(flowToken);
                    if (resp.isPresent()) {
                        sink.success(resp.get());
                        return;
                    }
                    completionBus.awaitSignal(POLL_INTERVAL.toMillis());
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    sink.error(e);
                    return;
                } catch (Exception e) {
                    sink.error(e);
                    return;
                }
            }
            actionLog.archiveFlow(flowToken);
            sink.success(addFlowTokenHeader(
                    io.micronaut.http.HttpResponse.serverError(TIMEOUT_MESSAGE),
                    flowToken));
        }).subscribeOn(reactor.core.scheduler.Schedulers.boundedElastic());
    }

    /**
     * Runs one quiescence iteration: poll concepts, flush completions,
     * fire syncs, repeat until no more syncs fire. Write batching reduces
     * transaction count: all concept completions within one iteration
     * commit in a single flush, and all sync invocations commit in a
     * single flush.
     */
    private void runTick() {
        boolean workDone;
        do {
            workDone = false;
            actionLog.beginBatch();
            runConceptAgents();
            actionLog.flushBatch();
            if (runSyncAgents()) {
                workDone = true;
            }
        } while (workDone);
    }

    private Optional<io.micronaut.http.HttpResponse<?>> buildResponse(String flowToken) {
        ResponseData data = checkForResponse(flowToken);
        if (data == null) return Optional.empty();
        actionLog.archiveFlow(flowToken);
        var httpStatus = io.micronaut.http.HttpStatus.valueOf(data.statusCode());
        return Optional.of(addFlowTokenHeader(
                io.micronaut.http.HttpResponse.status(httpStatus).body(data.fields()),
                flowToken));
    }

    private static <T> io.micronaut.http.MutableHttpResponse<T> addFlowTokenHeader(
            io.micronaut.http.MutableHttpResponse<T> response,
            String flowToken) {
        return response.header(FLOW_TOKEN_HEADER, flowToken);
    }

    private void runConceptAgents() {
        Set<String> targeted = drainPendingConcepts();
        if (targeted.isEmpty()) {
            for (ConceptAgent agent : conceptAgents) agent.pollAll();
        } else {
            for (String iri : targeted) {
                List<ConceptAgent> agents = pendingInvocationIndex.get(iri);
                if (agents != null) for (ConceptAgent agent : agents) agent.pollAll();
            }
        }
    }

    private Set<String> drainPendingConcepts() {
        if (pendingConcepts.isEmpty()) return Set.of();
        Set<String> snapshot = Set.copyOf(pendingConcepts);
        pendingConcepts.removeAll(snapshot);
        return snapshot;
    }

    /**
     * Fires syncs for every concept that completed work on this tick.
     * Returns true if any sync fired, so the caller can iterate until
     * quiescence.
     */
    private boolean runSyncAgents() {
        Set<String> triggered = completionBus.drainTriggeredConcepts();
        if (triggered.isEmpty()) return false;
        List<String> sparqlUpdates = new ArrayList<>();
        for (String conceptIri : triggered) {
            List<SyncAgent> relevant = triggerIndex.get(conceptIri);
            if (relevant != null) {
                for (SyncAgent agent : relevant) sparqlUpdates.add(agent.sparql());
            }
        }
        if (!sparqlUpdates.isEmpty()) {
            actionLog.updateBatch(sparqlUpdates);
            for (String conceptIri : triggered) {
                List<SyncAgent> relevant = triggerIndex.get(conceptIri);
                if (relevant != null) {
                    for (SyncAgent agent : relevant) {
                        String targetIri = agent.targetConceptIri();
                        if (targetIri != null && pendingInvocationIndex.containsKey(targetIri)) {
                            pendingConcepts.add(targetIri);
                        }
                    }
                }
            }
        }
        return !sparqlUpdates.isEmpty();
    }

    private ResponseData checkForResponse(String flowToken) {
        String sparql = "PREFIX : <" + SCHEMA + ">\n" +
                "SELECT ?pred ?value\n" +
                "WHERE {\n" +
                "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
                "    ?_action :concept <" + FlowManager.WEB_CONCEPT_IRI + "> ;\n" +
                "             :name \"respond\" ;\n" +
                "             :input ?_input ;\n" +
                "             :flow <" + flowToken + "> .\n" +
                "    ?_input ?pred ?value .\n" +
                "    FILTER (STRSTARTS(STR(?pred), \"" + SCHEMA + "\"))\n" +
                "  }\n" +
                "}\n";

        List<Map<String, String>> rows = actionLog.select(sparql);
        if (rows.isEmpty()) return null;

        String schemaStatusCode = SCHEMA + STATUS_CODE;
        Map<String, String> fields = new LinkedHashMap<>();
        int statusCode = 200;
        for (var row : rows) {
            String predUri = row.get("pred");
            String value = row.get("value");
            if (value == null) continue;
            if (schemaStatusCode.equals(predUri)) {
                statusCode = Integer.parseInt(value);
            } else {
                fields.put(predUri.substring(SCHEMA.length()), value);
            }
        }
        return new ResponseData(fields, statusCode);
    }

    private record ResponseData(Map<String, String> fields, int statusCode) {}
}
