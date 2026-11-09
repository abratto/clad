package dev.legible.bench.jmh;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import dev.legible.engine.Region;
import dev.legible.example.login.LoginApp;
import dev.legible.storage.LoginSchemas;
import dev.legible.storage.PostgresFactStore;
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
import org.openjdk.jmh.annotations.Warmup;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Durable-backend leg with the pool/store matrix the review needs:
 *
 * <ul>
 *   <li>{@code pool=simple} — {@link PGSimpleDataSource}, a new physical
 *       connection per operation (the original baseline).</li>
 *   <li>{@code pool=hikari} — a pooled {@link HikariDataSource}.</li>
 *   <li>{@code store=generic} — the generic fact relation
 *       ({@link PostgresFactStore}).</li>
 *   <li>{@code store=rmap} — the production R-map store
 *       ({@link RmapPostgresFactStore}).</li>
 * </ul>
 *
 * This separates the pooling gain from the store choice. Override the database
 * with {@code -Dpostgres.url} (and optional {@code postgres.user/password}) to
 * skip the Testcontainers startup; the schema must be clean or already created.
 */
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
@State(Scope.Benchmark)
@Fork(1)
@Warmup(iterations = 2, time = 1)
@Measurement(iterations = 3, time = 1)
public class PostgresBenchmark {

    @Param({"simple", "hikari"})
    private String pool;

    @Param({"generic", "rmap"})
    private String store;

    private PostgreSQLContainer<?> container;
    private HikariDataSource hikari;
    private LoginApp app;
    private Region region;
    private AtomicInteger sequence;

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

        DataSource dataSource;
        if ("hikari".equals(pool)) {
            HikariConfig config = new HikariConfig();
            config.setJdbcUrl(url);
            config.setUsername(user);
            config.setPassword(password);
            config.setMaximumPoolSize(Integer.getInteger("pg.poolSize", 10));
            config.setPoolName("jmh-postgres");
            hikari = new HikariDataSource(config);
            dataSource = hikari;
        } else {
            PGSimpleDataSource simple = new PGSimpleDataSource();
            simple.setUrl(url);
            simple.setUser(user);
            simple.setPassword(password);
            dataSource = simple;
        }

        if ("rmap".equals(store)) {
            RmapPostgresFactStore rmap = new RmapPostgresFactStore(dataSource, LoginSchemas.all());
            rmap.createSchema();
            app = LoginApp.create(rmap);
            region = rmap.region("UserNaming");
        } else {
            try (Connection connection = dataSource.getConnection();
                 Statement statement = connection.createStatement()) {
                statement.execute(PostgresFactStore.SCHEMA);
            }
            PostgresFactStore generic = new PostgresFactStore(dataSource);
            app = LoginApp.create(generic);
            region = generic.region("UserNaming");
        }

        app.seedUser("alice", "secret");
        // Unique usernames: the R-map schema derives a UNIQUE constraint on
        // username from the fact model, so duplicate values are rejected.
        for (int i = 0; i < 1000; i++) {
            region.write("s" + i, "username", "u" + i);
        }
        sequence = new AtomicInteger();
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
        return app.login("alice", "secret");
    }

    @Benchmark
    public Set<String> readHit() {
        return region.read("s500", "username");
    }

    @Benchmark
    public Set<String> readMiss() {
        return region.read("absent", "username");
    }

    @Benchmark
    public Set<String> subjects() {
        return region.subjects("username", "u3");
    }

    @Benchmark
    public void write() {
        int next = sequence.getAndIncrement();
        region.write("w" + next, "username", "w" + next);
    }
}
