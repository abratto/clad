package dev.legible.engine;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * In-memory {@link ActionLog}. Both maps are insertion-ordered, so
 * {@link #invocations(String)} returns actions in append (causal) order — the
 * engine appends each downstream invocation before it is processed.
 */
public final class InMemoryActionLog implements ActionLog {

    private final Map<String, Invocation> invocations = new LinkedHashMap<>();
    private final Map<String, Completion> completions = new LinkedHashMap<>();

    @Override
    public void appendInvocation(Invocation inv) {
        invocations.put(inv.actionId(), inv);
    }

    @Override
    public void appendCompletion(Completion comp) {
        completions.put(comp.actionId(), comp);
    }

    @Override
    public Optional<Invocation> invocation(String actionId) {
        return Optional.ofNullable(invocations.get(actionId));
    }

    @Override
    public Optional<Completion> completion(String actionId) {
        return Optional.ofNullable(completions.get(actionId));
    }

    @Override
    public List<Invocation> invocations() {
        return new ArrayList<>(invocations.values());
    }

    @Override
    public List<Invocation> invocations(String flowId) {
        List<Invocation> result = new ArrayList<>();
        for (Invocation inv : invocations.values()) {
            if (inv.flowId().equals(flowId)) result.add(inv);
        }
        return result;
    }

    @Override
    public boolean hasEmission(String parentActionId, String syncName) {
        for (Invocation inv : invocations.values()) {
            if (parentActionId.equals(inv.parentActionId())
                    && syncName.equals(inv.causedBySync())) {
                return true;
            }
        }
        return false;
    }

    @Override
    public Optional<Completion> completionByFlowAction(String flowId, String concept, String action) {
        for (Completion c : completions.values()) {
            if (c.flowId().equals(flowId) && c.concept().equals(concept) && c.action().equals(action)) {
                return Optional.of(c);
            }
        }
        return Optional.empty();
    }

    @Override
    public List<Completion> completions(String flowId) {
        List<Completion> result = new ArrayList<>();
        for (Completion c : completions.values()) {
            if (c.flowId().equals(flowId)) result.add(c);
        }
        return result;
    }

    @Override
    public Set<String> flowIds() {
        Set<String> ids = new LinkedHashSet<>();
        for (Invocation i : invocations.values()) ids.add(i.flowId());
        for (Completion c : completions.values()) ids.add(c.flowId());
        return ids;
    }

    @Override
    public void removeFlow(String flowId) {
        invocations.entrySet().removeIf(e -> e.getValue().flowId().equals(flowId));
        completions.entrySet().removeIf(e -> e.getValue().flowId().equals(flowId));
    }
}
