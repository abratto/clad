package dev.legible.engine;

/**
 * Destination for archived flow histories. The active action log is transient;
 * historical retention is the sink's job (mirrors {@code engine.archive.sink} in
 * the Jena profile: {@code logger} vs {@code devnull}).
 */
@FunctionalInterface
public interface FlowArchiveSink {

    FlowArchiveSink DEVNULL = flow -> { };

    void archive(FlowRecord flow);
}
