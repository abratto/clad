package dev.legible.bench.jmh;

import dev.legible.example.login.LoginApp;
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
 * Per-concept serialization: the engine serializes actions per concept
 * ({@code SyncEngine.execute}). {@code same} hammers one user (hot
 * {@code UserNaming}/{@code PasswordAuth}/{@code Session} regions); {@code unique}
 * seeds a fresh user per request, matching the existing concurrency driver.
 * Override the thread count with {@code -t} to sweep contention.
 */
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
@State(Scope.Benchmark)
@Fork(1)
@Threads(4)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
public class ConceptContentionBenchmark {

    @Param({"same", "unique"})
    private String mode;

    private LoginApp app;
    private AtomicInteger ids;

    @Setup(Level.Trial)
    public void setup() {
        app = LoginApp.create();
        app.seedUser("alice", "secret");
        ids = new AtomicInteger();
    }

    @Benchmark
    public Map<String, Object> login() {
        if ("same".equals(mode)) {
            return app.login("alice", "secret");
        }
        String username = "user-" + ids.getAndIncrement();
        app.seedUser(username, "pw");
        return app.login(username, "pw");
    }
}
