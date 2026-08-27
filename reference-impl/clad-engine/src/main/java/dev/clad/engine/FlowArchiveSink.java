package dev.clad.engine;

/**
 * Sink for archived flow triples. Implementations determine where the
 * N-Quads serialization of a completed flow's triples goes: a logger,
 * object storage, stdout, or nowhere.
 */
public interface FlowArchiveSink {

    /** Flush one completed flow's N-Quads payload. */
    void write(String flowToken, String nquads);

    /** Flush any buffered data. Called on shutdown. */
    default void close() {}

    /** Human-readable name for diagnostics. */
    String name();
}
