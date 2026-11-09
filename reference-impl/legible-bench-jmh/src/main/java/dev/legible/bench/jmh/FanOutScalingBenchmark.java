package dev.legible.bench.jmh;

import dev.legible.example.social.SocialApp;
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

import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Fan-out scaling: each comment notifies every follower of the commenting user
 * (a {@code fanOut} over {@code Following}) plus the post author. {@code N}
 * drives {@code WhereEvaluator} frame multiplication and the per-follower
 * {@code Notifying/notify} emission — the cost shape a linear login chain
 * cannot show.
 */
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
@State(Scope.Benchmark)
@Fork(1)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
public class FanOutScalingBenchmark {

    @Param({"1", "10", "100", "1000"})
    private int followers;

    private SocialApp app;
    private String postId;

    @Setup(Level.Trial)
    public void setup() {
        app = SocialApp.create();
        postId = app.publish("post-author", "the post").get("postId").toString();
        for (int i = 0; i < followers; i++) {
            app.seedFollow("f" + i, "commenter");
        }
    }

    @Benchmark
    public Map<String, Object> comment() {
        return app.comment(postId, "commenter", "hello");
    }
}
