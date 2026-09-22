package dev.legible.engine;

/**
 * Destination for archived flow histories. The active action log is transient;
 * historical retention is the sink's job. The default sink discards flows
 * ({@code DEVNULL}); a durable profile supplies its own sink.
 */
@FunctionalInterface
public interface FlowArchiveSink {

    FlowArchiveSink DEVNULL = flow -> { };

    void archive(FlowRecord flow);
}
