package dev.legible.bench.jmh;

import dev.legible.example.login.LoginApp;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Level;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;

import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Sequential end-to-end login throughput: the linear chain (request → lookup →
 * password check → session grant → respond) against the canonical in-memory
 * engine. Mirrors {@code dev.legible.bench.Bench} with JMH isolation.
 */
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
@State(Scope.Benchmark)
@Fork(1)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
public class LoginThroughputBenchmark {

    private LoginApp app;

    @Setup(Level.Trial)
    public void setup() {
        app = LoginApp.create();
        app.seedUser("alice", "secret");
    }

    @Benchmark
    public Map<String, Object> login() {
        return app.login("alice", "secret");
    }
}
