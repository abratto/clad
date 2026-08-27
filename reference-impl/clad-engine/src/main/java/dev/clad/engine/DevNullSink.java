package dev.clad.engine;

/**
 * Discards archived flow triples. Use when no historical retention is
 * needed — flows are deleted from the in-memory action log without
 * any external record.
 */
public class DevNullSink implements FlowArchiveSink {

    @Override
    public void write(String flowToken, String nquads) {
        // Intentionally empty — discard.
    }

    @Override
    public String name() { return "devnull"; }
}
