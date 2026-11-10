package dev.legible.bench.jmh;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import dev.legible.example.login.LoginApp;
import dev.legible.storage.LoginSchemas;
import dev.legible.storage.RmapPostgresFactStore;
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
import org.openjdk.jmh.annotations.TearDown;
import org.openjdk.jmh.annotations.Threads;
import org.openjdk.jmh.annotations.Warmup;
import org.testcontainers.containers.PostgreSQLContainer;

import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Production-path concurrency sweep: Hikari + {@link RmapPostgresFactStore}.
 *
 * <p>The engine serializes actions <em>per concept</em>, not per row or tenant.
 * {@code same} hammers one user; {@code unique} round-robins a pre-seeded user
 * set. Both hit the same three concept locks, so the benchmark shows whether
 * concurrency scales and where it plateaus. Sweep threads with {@code -t}:
 *
 * <pre>
 * java -jar target/benchmarks.jar -t 1  -p mode=same   'PostgresConcurrencyBenchmark.login'
 * java -jar target/benchmarks.jar -t 4  -p mode=unique 'PostgresConcurrencyBenchmark.login'
 * java -jar target/benchmarks.jar -t 16 -p mode=unique 'PostgresConcurrencyBenchmark.login'
 * </pre>
 *
 * Override the database with {@code -Dpostgres.url} (and optional
 * {@code postgres.user/password}) to skip the Testcontainers startup. The
 * schema must be clean or already created.
 */
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
@State(Scope.Benchmark)
@Fork(1)
@Threads(4)
@Warmup(iterations = 2, time = 1)
@Measurement(iterations = 3, time = 1)
public class PostgresConcurrencyBenchmark {

    @Param({"same", "unique"})
    private String mode;

    private PostgreSQLContainer<?> container;
    private HikariDataSource hikari;
    private LoginApp app;
    private AtomicInteger next;
    private String[] usernames;

    @Setup(Level.Trial)
    public void setup() throws Exception {
        String url;
        String user;
        String password;
        String externalUrl = System.getProperty("postgres.url");
        if (externalUrl != null && !externalUrl.isBlank()) {
            url = externalUrl;
            user = System.getProperty("postgres.user", "postgres");
            password = System.getProperty("postgres.password", "postgres");
        } else {
            container = new PostgreSQLContainer<>("postgres:16-alpine");
            container.start();
            url = container.getJdbcUrl();
            user = container.getUsername();
            password = container.getPassword();
        }

        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(user);
        config.setPassword(password);
        config.setMaximumPoolSize(Integer.getInteger("pg.poolSize", 10));
        config.setPoolName("jmh-postgres-concurrency");
        hikari = new HikariDataSource(config);

        RmapPostgresFactStore store = new RmapPostgresFactStore(hikari, LoginSchemas.all());
        store.createSchema();
        app = LoginApp.create(store);

        app.seedUser("alice", "secret");
        int users = Integer.getInteger("pg.users", 500);
        usernames = new String[users];
        for (int i = 0; i < users; i++) {
            usernames[i] = "u" + i;
            app.seedUser(usernames[i], "pw");
        }
        next = new AtomicInteger();
    }

    @TearDown(Level.Trial)
    public void tearDown() {
        if (hikari != null) {
            hikari.close();
        }
        if (container != null) {
            container.stop();
        }
    }

    @Benchmark
    public Map<String, Object> login() {
        if ("same".equals(mode)) {
            return app.login("alice", "secret");
        }
        int index = Math.floorMod(next.getAndIncrement(), usernames.length);
        String username = usernames[index];
        return app.login(username, "pw");
    }
}
