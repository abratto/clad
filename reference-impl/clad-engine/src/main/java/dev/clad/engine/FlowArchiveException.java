package dev.clad.engine;

/**
 * Thrown when FlowArchiver cannot flush action log triples to the
 * configured log backend. The triples remain in the in-memory action
 * log — they are NOT deleted. Fix the log backend and retry.
 */
public class FlowArchiveException extends RuntimeException {
    public FlowArchiveException(String message, Throwable cause) {
        super(message, cause);
    }
}
