package dev.legible.bench.concurrency;

import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Level;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Threads;
import org.openjdk.jmh.annotations.Warmup;

import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * JMH throughput for the concurrency lab: {@code same} (one hot counter),
 * {@code unique} (round-robin counters), and {@code transfer} (multi-subject).
 * In-memory only; use {@link ConcurrencyLabProbe} for the Rmap correctness leg.
 */
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
@State(Scope.Benchmark)
@Fork(1)
@Threads(4)
@Warmup(iterations = 2, time = 1)
@Measurement(iterations = 3, time = 1)
public class ConcurrencyLabBenchmark {

    @Param({"same", "unique", "transfer"})
    private String mode;

    private ConcurrencyLabApp app;
    private AtomicInteger next;

    @Setup(Level.Trial)
    public void setup() {
        app = ConcurrencyLabApp.create();
        app.seedBalance("from", 1_000_000);
        app.seedBalance("to", 1_000_000);
        next = new AtomicInteger();
    }

    @Benchmark
    public Map<String, Object> op() {
        return switch (mode) {
            case "same" -> app.increment("hot");
            case "unique" -> app.increment("c" + Math.floorMod(next.getAndIncrement(), 64));
            case "transfer" -> app.transfer("from", "to", 1);
            default -> throw new IllegalStateException("unknown mode: " + mode);
        };
    }
}
