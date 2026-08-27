package dev.legible.engine;

import java.util.ArrayDeque;
import java.util.List;
import java.util.Optional;

/**
 * A bounded, in-memory ring of recently completed flows for debug inspection.
 * Mirrors {@code engine.archive.buffer.size} in the Jena profile; a capacity of
 * 0 disables retention.
 */
public final class FlowArchiveBuffer {

    private final int capacity;
    private final ArrayDeque<FlowRecord> recent = new ArrayDeque<>();

    public FlowArchiveBuffer(int capacity) {
        this.capacity = capacity;
    }

    public synchronized void add(FlowRecord flow) {
        if (capacity <= 0) return;
        recent.addLast(flow);
        while (recent.size() > capacity) {
            recent.removeFirst();
        }
    }

    public synchronized List<FlowRecord> recent() {
        return List.copyOf(recent);
    }

    public synchronized Optional<FlowRecord> latest() {
        return recent.isEmpty() ? Optional.empty() : Optional.of(recent.getLast());
    }

    public synchronized Optional<FlowRecord> find(String flowId) {
        return recent.stream().filter(f -> f.flowId().equals(flowId)).findFirst();
    }
}
