package dev.clad.engine;

import jakarta.inject.Singleton;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Evaluates synchronization rules as declarative predicates over the combined
 * action space.
 *
 * <p>A concept's {@code writeCompletion()} asks this evaluator "which syncs
 * match this outcome?" <em>before</em> the concept commits. If no sync matches
 * and the action is not {@code Web/respond}, the concept rejects the completion
 * before any state is modified.
 *
 * <p>This implements the WYSIWID paper's semantics: synchronizations are
 * predicates over combined state/action space, evaluated at completion time.
 * A→B writes happen in one Jena transaction (via the concept's
 * {@code beginBatch}/{@code flushBatch}) so the composite transition commits
 * or rolls back atomically.
 */
@Singleton
public class SyncEvaluator {

    private static final Logger LOG = LoggerFactory.getLogger(SyncEvaluator.class);

    private final Map<String, List<SyncAgent>> triggerIndex;

    public SyncEvaluator(List<SyncAgent> allSyncs) {
        this.triggerIndex = new ConcurrentHashMap<>();
        for (SyncAgent sync : allSyncs) {
            SyncTrigger trigger = sync.trigger();
            String key = triggerKey(trigger.conceptIri(), trigger.actionName());
            triggerIndex.computeIfAbsent(key, k -> new ArrayList<>()).add(sync);
        }
        LOG.info("Sync evaluator: {} sync(s) across {} trigger(s)",
                allSyncs.size(), triggerIndex.size());
    }

    /**
     * Evaluates which syncs match a proposed completion. Called BEFORE the
     * concept writes its completion — the outcome is validated against the
     * sync rules before any state is modified.
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
