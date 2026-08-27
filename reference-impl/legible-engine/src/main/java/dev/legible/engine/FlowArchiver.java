package dev.legible.engine;

import java.util.List;

/**
 * Moves a completed flow out of its transient per-flow log and into a sink plus
 * a bounded buffer. The action log is transient execution state — not durable
 * business state — so sharding it per flow is purely an in-memory concurrency
 * concern and never touches persistence.
 */
public final class FlowArchiver {

    private final FlowArchiveSink sink;
    private final FlowArchiveBuffer buffer;

    public FlowArchiver(FlowArchiveSink sink, FlowArchiveBuffer buffer) {
        this.sink = sink;
        this.buffer = buffer;
    }

    public FlowArchiveBuffer buffer() {
        return buffer;
    }

    /** Flush one flow's history to the sink + buffer. */
    public void archive(String flowId, ActionLog flowLog) {
        List<Invocation> invs = flowLog.invocations(flowId);
        List<Completion> comps = flowLog.completions(flowId);
        if (invs.isEmpty() && comps.isEmpty()) return;
        FlowRecord record = new FlowRecord(flowId, List.copyOf(invs), List.copyOf(comps));
        buffer.add(record);
        sink.archive(record);
    }
}
