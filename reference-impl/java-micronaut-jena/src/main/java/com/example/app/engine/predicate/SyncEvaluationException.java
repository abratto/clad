package com.example.app.engine.predicate;

/**
 * Thrown when a concept attempts to write a completion with an outcome
 * that no synchronization predicate matches.
 *
 * <p>In the reference engine, any outcome can be committed — the dispatcher
 * simply won't fire any syncs. In the predicate engine, an unmatched outcome
 * is a protocol violation: if no sync handles it, the system has no way to
 * produce a valid response, and the action should be rejected before state
 * mutation.
 *
 * <p>Web/respond is exempt from this requirement — it is the terminal action
 * and always succeeds.
 */
public class SyncEvaluationException extends RuntimeException {

    public SyncEvaluationException(String message) {
        super(message);
    }

    public SyncEvaluationException(String message, Throwable cause) {
        super(message, cause);
    }
}
