package dev.legible.bench.jmh;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import dev.legible.engine.Concept;
import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.SyncEngine;
import dev.legible.example.login.LoginSyncs;
import dev.legible.example.login.PasswordAuthConcept;
import dev.legible.example.login.SessionConcept;
import dev.legible.example.login.UserNamingConcept;
import dev.legible.example.login.WebConcept;
import dev.legible.storage.LoginSchemas;
import dev.legible.storage.PostgresFactStore;
import dev.legible.storage.RmapPostgresFactStore;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Step 0 probe: attributes login latency to concepts and region operations.
 *
 * <p>No engine change. Wraps every concept and region with a timer, runs a
 * fixed number of logins at each thread level, and prints count, total time,
 * average time, and utilisation ({@code total / wall}) so the critical concept
 * lock can be identified before per-subject locking.
 *
 * <pre>
 * java -cp target/benchmarks.jar dev.legible.bench.jmh.ConceptTimingProbe \
 *   -Dprobe.store=rmap -Dprobe.pool=hikari -Dprobe.users=unique \
 *   -Dprobe.threads=1,4 -Dprobe.requests=2000
 * </pre>
 */
public final class ConceptTimingProbe {

    private ConceptTimingProbe() {
    }

    public static void main(String[] args) throws Exception {
        String pool = System.getProperty("probe.pool", "hikari");
        String storeKind = System.getProperty("probe.store", "rmap");
        String userMode = System.getProperty("probe.users", "same");
        int requests = Integer.getInteger("probe.requests", 2000);
        int warmup = Integer.getInteger("probe.warmup", 500);
        int userCount = Integer.getInteger("probe.userCount", 200);
        List<Integer> threadLevels = parseThreads(System.getProperty("probe.threads", "1,4"));

        PostgreSQLContainer<?> container = null;
        HikariDataSource hikari = null;
        FactStore rawStore;

        if ("memory".equals(storeKind)) {
            rawStore = new InMemoryFactStore();
        } else {
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
                config.setPoolName("probe-postgres");
                hikari = new HikariDataSource(config);
                dataSource = hikari;
            } else {
                PGSimpleDataSource simple = new PGSimpleDataSource();
                simple.setUrl(url);
                simple.setUser(user);
                simple.setPassword(password);
                dataSource = simple;
            }

            if ("rmap".equals(storeKind)) {
                RmapPostgresFactStore rmap = new RmapPostgresFactStore(dataSource, LoginSchemas.all());
                rmap.createSchema();
                rawStore = rmap;
            } else {
                try (Connection connection = dataSource.getConnection();
                     Statement statement = connection.createStatement()) {
                    statement.execute(PostgresFactStore.SCHEMA);
                }
                rawStore = new PostgresFactStore(dataSource);
            }
        }

        TimingStats stats = new TimingStats();
        TimingFactStore facts = new TimingFactStore(rawStore, stats);

        UserNamingConcept userNaming = new UserNamingConcept(facts.region("UserNaming"));
        PasswordAuthConcept passwordAuth = new PasswordAuthConcept(facts.region("PasswordAuth"));
        SessionConcept session = new SessionConcept(facts.region("Session"));
        List<Concept> concepts = List.of(
                new TimingConcept(new WebConcept(), stats),
                new TimingConcept(userNaming, stats),
                new TimingConcept(passwordAuth, stats),
                new TimingConcept(session, stats));
        SyncEngine engine = new SyncEngine(facts, concepts, LoginSyncs.all());

        userNaming.seedUser("uid-alice", "alice");
        passwordAuth.seedCredential("uid-alice", "secret");
        String[] usernames = new String[userCount];
        for (int i = 0; i < userCount; i++) {
            usernames[i] = "u" + i;
            String userId = "uid-" + i;
            userNaming.seedUser(userId, usernames[i]);
            passwordAuth.seedCredential(userId, "pw");
        }
        stats.reset();

        AtomicInteger warmupIndex = new AtomicInteger();
        for (int i = 0; i < warmup; i++) {
            login(engine, userMode, usernames, warmupIndex);
        }
        stats.reset();

        System.out.printf("=== probe pool=%s store=%s users=%s requests=%d ===%n",
                pool, storeKind, userMode, requests);
        for (int threadCount : threadLevels) {
            run(engine, userMode, usernames, requests, threadCount, stats);
        }

        if (hikari != null) {
            hikari.close();
        }
        if (container != null) {
            container.stop();
        }
    }

    private static void run(SyncEngine engine, String userMode, String[] usernames,
                            int requests, int threads, TimingStats stats)
            throws InterruptedException {
        stats.reset();
        int perThread = Math.max(1, requests / threads);
        int total = perThread * threads;
        AtomicInteger userIndex = new AtomicInteger();
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);

        for (int t = 0; t < threads; t++) {
            Thread thread = new Thread(() -> {
                try {
                    start.await();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                for (int i = 0; i < perThread; i++) {
                    login(engine, userMode, usernames, userIndex);
                }
                done.countDown();
            }, "probe-" + t);
            thread.start();
        }

        long wallStart = System.nanoTime();
        start.countDown();
        done.await();
        long wallNanos = System.nanoTime() - wallStart;
        double seconds = wallNanos / 1e9;

        System.out.printf("%n--- threads=%d total=%d wall=%.3fs throughput=%.0f req/s ---%n",
                threads, total, seconds, total / seconds);
        print(stats, wallNanos, "action:");
        print(stats, wallNanos, "region:");
    }

    private static void login(SyncEngine engine, String userMode, String[] usernames,
                              AtomicInteger index) {
        String username;
        String password;
        if ("same".equals(userMode)) {
            username = "alice";
            password = "secret";
        } else {
            int i = Math.floorMod(index.getAndIncrement(), usernames.length);
            username = usernames[i];
            password = "pw";
        }
        engine.run("Web", "request", Map.of(
                "route", "login",
                "username", username,
                "password", password));
    }

    private static void print(TimingStats stats, long wallNanos, String prefix) {
        System.out.printf("%-42s %8s %12s %10s %8s%n",
                "key", "count", "total_ms", "avg_us", "util");
        for (TimingStats.Entry entry : stats.entries()) {
            if (!entry.key().startsWith(prefix)) {
                continue;
            }
            System.out.printf("%-42s %8d %12.2f %10.2f %8.2f%n",
                    entry.key(), entry.count(), entry.totalMillis(),
                    entry.avgMicros(), entry.utilization(wallNanos));
        }
    }

    private static List<Integer> parseThreads(String csv) {
        List<Integer> out = new ArrayList<>();
        for (String part : csv.split(",")) {
            String trimmed = part.trim();
            if (!trimmed.isEmpty()) {
                out.add(Integer.parseInt(trimmed));
            }
        }
        return out;
    }
}
