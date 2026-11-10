package dev.legible.bench.jmh;

import dev.legible.engine.Concept;

import java.util.Map;
import java.util.Set;

/** Times one concept's action executions for the Step 0 probe. */
public final class TimingConcept implements Concept {

    private final Concept delegate;
    private final TimingStats stats;

    public TimingConcept(Concept delegate, TimingStats stats) {
        this.delegate = delegate;
        this.stats = stats;
    }

    @Override
    public String name() {
        return delegate.name();
    }

    @Override
    public boolean stateful() {
        return delegate.stateful();
    }

    @Override
    public Object lockKey(String action, Map<String, Object> input) {
        return delegate.lockKey(action, input);
    }

    @Override
    public Set<Object> lockKeys(String action, Map<String, Object> input) {
        return delegate.lockKeys(action, input);
    }

    @Override
    public Map<String, Object> execute(String action, Map<String, Object> input) {
        long start = System.nanoTime();
        try {
            return delegate.execute(action, input);
        } finally {
            stats.record("action:" + delegate.name() + "/" + action,
                    System.nanoTime() - start);
        }
    }

    public Concept delegate() {
        return delegate;
    }
}
