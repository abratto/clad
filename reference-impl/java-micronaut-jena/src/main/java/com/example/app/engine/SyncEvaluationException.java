package com.example.app.engine;

/**
 * Thrown when a concept attempts to write a completion with an outcome
 * that no synchronization predicate matches.
 *
 * <p>An unmatched outcome is a protocol violation: if no sync handles it,
 * the system has no way to produce a valid response, and the action should be
 * rejected before state mutation. This is the paper's predicate model — an
 * action is only valid if at least one synchronization predicate is satisfied
 * by its outcome.
 *
 * <p>{@code Web/respond} is exempt — it is the terminal action and always
 * succeeds.
 */
public class SyncEvaluationException extends RuntimeException {

    public SyncEvaluationException(String message) {
        super(message);
    }

    public SyncEvaluationException(String message, Throwable cause) {
        super(message, cause);
    }
}
