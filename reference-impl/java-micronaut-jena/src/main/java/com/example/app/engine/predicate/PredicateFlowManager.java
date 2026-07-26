package com.example.app.engine.predicate;

import com.example.app.engine.ActionLog;
import com.example.app.engine.CompletionBus;
import com.example.app.engine.FlowManager;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Predicate-aware FlowManager.
 *
 * <p>Functionally identical to {@link FlowManager} — mints flow tokens and
 * writes root Web/request actions. The predicate enforcement lives in
 * {@link PredicateConceptAgent}, which ensures that the Web concept
 * (processed as a normal concept under the predicate engine) has its
 * {@code [routed]} outcome matched by syncs.
 *
 * <p>This subclass exists so the DI container can choose it when
 * {@code engine.mode=predicate} is configured. It adds no new behavior
 * beyond what FlowManager provides.
 */
@Singleton
public class PredicateFlowManager extends FlowManager {

    @Inject
    public PredicateFlowManager(ActionLog actionLog, CompletionBus completionBus) {
        super(actionLog, completionBus);
    }
}
