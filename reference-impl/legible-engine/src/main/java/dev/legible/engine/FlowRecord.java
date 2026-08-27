package dev.legible.engine;

import java.util.List;

/**
 * A snapshot of one completed flow's history, produced at archival time. The
 * active log is transient; once a flow reaches quiescence it is flushed here
 * (and to a {@link FlowArchiveSink}) and removed from the active log.
 */
public record FlowRecord(
        String flowId,
        List<Invocation> invocations,
        List<Completion> completions) {
}
