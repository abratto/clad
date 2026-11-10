package dev.legible.bench.concurrency;

import dev.legible.engine.Concept;
import dev.legible.engine.Region;

import java.util.Map;

/** Lab concept: a single read-modify-write counter keyed by {@code counterId}. */
public final class CounterConcept implements Concept {

    public static final String NAME = "Counter";
    public static final String INCREMENT = "increment";

    private final Region region;

    public CounterConcept(Region region) {
        this.region = region;
    }

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public Object lockKey(String action, Map<String, Object> input) {
        return INCREMENT.equals(action) ? input.get("counterId") : null;
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        if (!INCREMENT.equals(action)) {
            return Map.of("outcome", "error", "message", "unknown action: " + action);
        }
        String counterId = (String) input.get("counterId");
        if (counterId == null) {
            return Map.of("outcome", "error", "message", "missing counterId");
        }
        int next = current(counterId) + 1;
        region.clear(counterId, "count");
        region.write(counterId, "count", String.valueOf(next));
        return Map.of("outcome", "INCREMENTED", "counterId", counterId, "count", next);
    }

    public int current(String counterId) {
        var values = region.read(counterId, "count");
        return values.isEmpty() ? 0 : Integer.parseInt(values.iterator().next());
    }
}
