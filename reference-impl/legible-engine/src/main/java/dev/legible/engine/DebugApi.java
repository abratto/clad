package dev.legible.engine;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Developer-mode introspection over in-flight flow logs, the archive buffer,
 * the fact store, and the registered sync rules.
 *
 * <p>The Jena profile exposed the same surface as SPARQL queries against the RDF
 * action graph. Here the data is already structured, so each endpoint is a
 * direct lookup over {@link Invocation}/{@link Completion}/{@link Fact} records.
 */
public final class DebugApi {

    private final Map<String, ActionLog> inFlight;
    private final FactStore facts;
    private final List<SyncRule> rules;
    private final FlowArchiveBuffer buffer;

    public DebugApi(Map<String, ActionLog> inFlight, FactStore facts,
                    List<SyncRule> rules, FlowArchiveBuffer buffer) {
        this.inFlight = inFlight;
        this.facts = facts;
        this.rules = rules;
        this.buffer = buffer;
    }

    /** {@code GET /api/dev/flow/{flowId}} — in-flight log, with archive-buffer fallback. */
    public Map<String, Object> flow(String flowId) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("flowId", flowId);

        List<Map<String, Object>> actions;
        String source;
        ActionLog active = inFlight.get(flowId);
        if (active != null) {
            actions = flowActions(active, flowId);
            source = "active-log";
        } else if (buffer != null && buffer.find(flowId).isPresent()) {
            actions = flowActions(buffer.find(flowId).get());
            source = "archive-buffer";
        } else {
            actions = List.of();
            source = "none";
        }
        response.put("source", source);
        response.put("actionCount", actions.size());
        response.put("actions", actions);
        if (actions.isEmpty()) {
            response.put("warning", "No actions found in active log or archive buffer.");
        }
        return response;
    }

    /** {@code GET /api/dev/stuck} — in-flight invocations committed with no completion yet. */
    public Map<String, Object> stuck() {
        List<Map<String, Object>> stuck = new ArrayList<>();
        for (Map.Entry<String, ActionLog> e : inFlight.entrySet()) {
            for (Invocation i : e.getValue().invocations(e.getKey())) {
                if (e.getValue().completion(i.actionId()).isEmpty()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("actionId", i.actionId());
                    row.put("flowId", i.flowId());
                    row.put("concept", i.concept());
                    row.put("action", i.action());
                    stuck.add(row);
                }
            }
        }
        stuck.sort(Comparator.comparing(m -> (String) m.get("actionId")));

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("stuckCount", stuck.size());
        response.put("stuck", stuck);
        response.put("status", stuck.isEmpty()
                ? "No active actions are missing an outcome."
                : stuck.size() + " active action(s) are missing an outcome.");
        return response;
    }

    /** {@code GET /api/dev/concept/{name}/facts} — dump a concept's own region. */
    public Map<String, Object> concept(String name) {
        List<Map<String, Object>> rows = facts.region(name).facts().stream()
                .sorted(Comparator.comparing(Fact::subject)
                        .thenComparing(Fact::predicate)
                        .thenComparing(Fact::value))
                .map(f -> {
                    Map<String, Object> e = new LinkedHashMap<>();
                    e.put("subject", f.subject());
                    e.put("predicate", f.predicate());
                    e.put("value", f.value());
                    return e;
                })
                .toList();
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("concept", name);
        response.put("factCount", rows.size());
        response.put("facts", rows);
        return response;
    }

    /** {@code GET /api/dev/syncs} — the registered sync rules. */
    public List<Map<String, Object>> syncs() {
        return rules.stream()
                .map(r -> {
                    Map<String, Object> e = new LinkedHashMap<>();
                    e.put("name", r.name);
                    e.put("trigger", r.triggerConcept + "/" + r.triggerAction
                            + (r.triggerOutcome == null ? "" : "[" + r.triggerOutcome + "]"));
                    e.put("then", r.then.stream().map(t -> t.concept() + "/" + t.action()).toList());
                    return e;
                })
                .toList();
    }

    private List<Map<String, Object>> flowActions(ActionLog log, String flowId) {
        Map<String, Completion> byId = log.completions(flowId).stream()
                .collect(Collectors.toMap(Completion::actionId, Function.identity()));
        return log.invocations(flowId).stream()
                .map(inv -> actionEntry(inv, byId.get(inv.actionId())))
                .toList();
    }

    private List<Map<String, Object>> flowActions(FlowRecord rec) {
        Map<String, Completion> byId = rec.completions().stream()
                .collect(Collectors.toMap(Completion::actionId, Function.identity()));
        return rec.invocations().stream()
                .map(inv -> actionEntry(inv, byId.get(inv.actionId())))
                .toList();
    }

    private Map<String, Object> actionEntry(Invocation inv, Completion comp) {
        Map<String, Object> e = new LinkedHashMap<>();
        e.put("actionId", inv.actionId());
        e.put("concept", inv.concept());
        e.put("action", inv.action());
        e.put("input", inv.input());
        if (inv.parentActionId() != null) e.put("parentActionId", inv.parentActionId());
        if (inv.causedBySync() != null) e.put("causedBySync", inv.causedBySync());
        e.put("invokedAt", inv.invokedAt());
        if (comp != null) {
            e.put("outcome", comp.outcome());
            e.put("fields", comp.fields());
            e.put("completedAt", comp.completedAt());
        }
        return e;
    }
}
