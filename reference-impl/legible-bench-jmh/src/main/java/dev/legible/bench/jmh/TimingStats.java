package dev.legible.bench.jmh;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** Per-key timing aggregates for the Step 0 concept/region probe. */
public final class TimingStats {

    public record Entry(String key, long count, long totalNanos) {
        public double totalMillis() {
            return totalNanos / 1_000_000.0;
        }

        public double avgMicros() {
            return count == 0 ? 0 : totalNanos / 1_000.0 / count;
        }

        public double utilization(long wallNanos) {
            return wallNanos == 0 ? 0 : (double) totalNanos / wallNanos;
        }
    }

    private final ConcurrentHashMap<String, LongAdder> nanos = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, LongAdder> counts = new ConcurrentHashMap<>();

    public void record(String key, long durationNanos) {
        nanos.computeIfAbsent(key, k -> new LongAdder()).add(durationNanos);
        counts.computeIfAbsent(key, k -> new LongAdder()).increment();
    }

    public List<Entry> entries() {
        List<Entry> out = new ArrayList<>();
        for (String key : nanos.keySet()) {
            out.add(new Entry(key, counts.get(key).sum(), nanos.get(key).sum()));
        }
        out.sort(Comparator.comparingLong(Entry::totalNanos).reversed());
        return out;
    }

    public void reset() {
        nanos.clear();
        counts.clear();
    }
}
