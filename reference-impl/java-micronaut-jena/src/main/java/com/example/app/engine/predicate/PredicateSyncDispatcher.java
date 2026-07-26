package com.example.app.engine.predicate;

import com.example.app.engine.ActionLog;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Predicate-based sync dispatcher — evaluates synchronization rules
 * as declarative predicates rather than imperative event handlers.
 *
 * <h3>How it differs from the reference engine</h3>
 *
 * <p>In the reference engine, the dispatcher polls the action log for
 * completed actions and fires matching syncs asynchronously. Actions
 * commit independently — there is a window between A completing and B
 * being invoked.
 *
 * <p>In the predicate engine, sync evaluation happens BEFORE the concept
 * commits. The concept's {@code writeCompletion()} asks this dispatcher
 * "which syncs match this outcome?" If no sync matches and the action
 * isn't Web/respond, the action is rejected before any state is modified.
 *
 * <p>This implements the paper's semantics: synchronizations are predicates
 * over combined state/action space, evaluated at completion time. A→B
 * writes still happen sequentially (separate Jena transactions) until a
 * shared-transaction API exists in the ActionLog.
 */
@Singleton
public class PredicateSyncDispatcher {

    private static final Logger LOG = LoggerFactory.getLogger(PredicateSyncDispatcher.class);

    private final Map<String, List<SyncAgent>> triggerIndex;

    @Inject
    public PredicateSyncDispatcher(ActionLog actionLog, List<SyncAgent> allSyncs) {
        this.triggerIndex = new java.util.concurrent.ConcurrentHashMap<>();

        for (SyncAgent sync : allSyncs) {
            SyncTrigger trigger = sync.trigger();
            String key = triggerKey(trigger.conceptIri(), trigger.actionName());
            triggerIndex.computeIfAbsent(key, k -> new ArrayList<>()).add(sync);
        }
        LOG.info("Predicate engine: {} sync(s) across {} trigger(s)",
                allSyncs.size(), triggerIndex.size());
    }

    /**
     * Evaluates which syncs match a proposed completion. Called BEFORE
     * the concept writes its completion — the outcome is validated
     * against the sync rules before any state is modified.
     *
     * @return list of matching syncs. If empty and the action is not
     *         Web/respond, the concept MUST reject the completion.
     */
    public List<SyncAgent> evaluateSyncs(
            String conceptIri, String actionName, String outcome) {

        String key = triggerKey(conceptIri, actionName);
        List<SyncAgent> candidates = triggerIndex.getOrDefault(key, Collections.emptyList());

        List<SyncAgent> matched = new ArrayList<>();
        for (SyncAgent sync : candidates) {
            SyncTrigger trigger = sync.trigger();
            if (trigger.outputStatus() == null
                    || trigger.outputStatus().equals(outcome)) {
                matched.add(sync);
            }
        }
        return matched;
    }

    static String triggerKey(String conceptIri, String actionName) {
        return conceptIri + "::" + actionName;
    }
}
