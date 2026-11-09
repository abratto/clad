package dev.legible.bench.jmh;

import dev.legible.engine.Fact;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.Region;
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
import org.openjdk.jmh.annotations.Warmup;

import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Region primitives: the suspected in-memory hotspots. {@code readHit} pays a
 * value-set copy; {@code readMiss} triggers the composite-prefix full-region
 * scan; {@code subjects} is the fan-out adjacency scan; {@code facts} is the
 * {@code scan()} source.
 */
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
@State(Scope.Benchmark)
@Fork(1)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
public class RegionMicroBenchmark {

    @Param({"1000", "10000"})
    private int subjects;

    private Region region;
    private String hit;

    @Setup(Level.Trial)
    public void setup() {
        region = new InMemoryFactStore().region("Micro");
        for (int i = 0; i < subjects; i++) {
            region.write("s" + i, "p", "v" + (i % 10));
        }
        hit = "s" + (subjects / 2);
    }

    @Benchmark
    public Set<String> readHit() {
        return region.read(hit, "p");
    }

    @Benchmark
    public Set<String> readMiss() {
        return region.read("absent", "p");
    }

    @Benchmark
    public Set<String> subjects() {
        return region.subjects("p", "v3");
    }

    @Benchmark
    public List<Fact> facts() {
        return region.facts();
    }
}
