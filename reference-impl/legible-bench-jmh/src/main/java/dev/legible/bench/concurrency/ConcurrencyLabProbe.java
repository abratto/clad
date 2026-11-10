package dev.legible.bench.concurrency;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import dev.legible.storage.RmapPostgresFactStore;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import javax.sql.DataSource;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.IntConsumer;

/**
 * Throwaway correctness probe for the per-subject locking strategy.
 *
 * <p>Scenarios: one hot counter (same subject), per-thread counters/accounts
 * (unique subjects), and concurrent transfers between overlapping accounts
 * (multi-subject, ordered acquisition). The transfer scenario also proves there
 * is no deadlock: every future has a timeout.
 *
 * <pre>
 * java -cp target/benchmarks.jar dev.legible.bench.concurrency.ConcurrencyLabProbe \
 *   -Dlab.store=memory -Dlab.threads=1,4 -Dlab.ops=1000
 * java -cp target/benchmarks.jar dev.legible.bench.concurrency.ConcurrencyLabProbe \
 *   -Dlab.store=rmap -Dlab.pool=hikari -Dlab.threads=1,4 -Dlab.ops=1000
 * </pre>
 */
public final class ConcurrencyLabProbe {

    private ConcurrencyLabProbe() {
    }

    public static void main(String[] args) throws Exception {
        String storeKind = System.getProperty("lab.store", "memory");
        String pool = System.getProperty("lab.pool", "hikari");
        List<Integer> threadLevels = parseThreads(System.getProperty("lab.threads", "1,4"));
        int ops = Integer.getInteger("lab.ops", 1000);
        int accounts = Integer.getInteger("lab.accounts", 10);

        PostgreSQLContainer<?> container = null;
        HikariDataSource hikari = null;
        FactStore facts;

        if ("memory".equals(storeKind)) {
            facts = new InMemoryFactStore();
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
                config.setPoolName("lab-postgres");
                hikari = new HikariDataSource(config);
                dataSource = hikari;
            } else {
                PGSimpleDataSource simple = new PGSimpleDataSource();
                simple.setUrl(url);
                simple.setUser(user);
                simple.setPassword(password);
                dataSource = simple;
            }
            RmapPostgresFactStore rmap =
                    new RmapPostgresFactStore(dataSource, ConcurrencyLabSchemas.all());
            rmap.createSchema();
            facts = rmap;
        }

        ConcurrencyLabApp app = ConcurrencyLabApp.create(facts);
        System.out.printf("=== lab store=%s pool=%s ops=%d accounts=%d ===%n",
                storeKind, pool, ops, accounts);
        warmup(app);

        for (int threads : threadLevels) {
            System.out.printf("%n--- threads=%d ---%n", threads);
            counterSame(app, threads, ops);
            counterUnique(app, threads, ops);
            accountUnique(app, threads, ops);
            transfer(app, threads, ops, accounts);
        }

        if (hikari != null) {
            hikari.close();
        }
        if (container != null) {
            container.stop();
        }
    }

    private static void warmup(ConcurrencyLabApp app) {
        for (int i = 0; i < 200; i++) {
            app.increment("warm-counter");
        }
        for (int i = 0; i < 200; i++) {
            app.credit("warm-account", 1);
        }
        app.seedBalance("warm-from", 1_000_000);
        app.seedBalance("warm-to", 1_000_000);
        for (int i = 0; i < 200; i++) {
            app.transfer("warm-from", "warm-to", 1);
        }
    }

    private static void counterSame(ConcurrencyLabApp app, int threads, int ops)
            throws Exception {
        String id = "hot-" + threads;
        long wall = run(threads, ops, ignored -> app.increment(id));
        int expected = threads * ops;
        int actual = app.counterValue(id);
        report("counterSame", wall, expected, expected, actual);
        if (actual != expected) {
            throw new AssertionError("counterSame lost increments: expected "
                    + expected + " but was " + actual);
        }
    }

    private static void counterUnique(ConcurrencyLabApp app, int threads, int ops)
            throws Exception {
        long wall = run(threads, ops, index -> {
            int thread = index / ops;
            app.increment("c" + threads + "-" + thread);
        });
        int actual = 0;
        for (int t = 0; t < threads; t++) {
            actual += app.counterValue("c" + threads + "-" + t);
        }
        int expected = threads * ops;
        report("counterUnique", wall, expected, expected, actual);
        if (actual != expected) {
            throw new AssertionError("counterUnique lost increments: expected "
                    + expected + " but was " + actual);
        }
    }

    private static void accountUnique(ConcurrencyLabApp app, int threads, int ops)
            throws Exception {
        long wall = run(threads, ops, index -> {
            int thread = index / ops;
            app.credit("a" + threads + "-" + thread, 1);
        });
        int actual = 0;
        for (int t = 0; t < threads; t++) {
            actual += app.balance("a" + threads + "-" + t);
        }
        int expected = threads * ops;
        report("accountUnique", wall, expected, expected, actual);
        if (actual != expected) {
            throw new AssertionError("accountUnique lost credits: expected "
                    + expected + " but was " + actual);
        }
    }

    private static void transfer(ConcurrencyLabApp app, int threads, int ops, int accounts)
            throws Exception {
        int start = 1_000_000;
        for (int i = 0; i < accounts; i++) {
            app.seedBalance("t" + threads + "-" + i, start);
        }
        long wall = run(threads, ops, index -> {
            int from = index % accounts;
            int to = (index + 1) % accounts;
            Map<String, Object> response =
                    app.transfer("t" + threads + "-" + from, "t" + threads + "-" + to, 1);
            if (Integer.valueOf(409).equals(response.get("status"))) {
                throw new IllegalStateException("unexpected insufficient funds");
            }
        });
        int total = 0;
        int min = Integer.MAX_VALUE;
        for (int i = 0; i < accounts; i++) {
            int balance = app.balance("t" + threads + "-" + i);
            total += balance;
            min = Math.min(min, balance);
        }
        int expected = accounts * start;
        report("transfer", wall, threads * ops, expected, total);
        if (total != expected) {
            throw new AssertionError("transfer broke the total: expected "
                    + expected + " but was " + total);
        }
        if (min < 0) {
            throw new AssertionError("transfer produced a negative balance: " + min);
        }
    }

    private static long run(int threads, int ops, IntConsumer action) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        CountDownLatch start = new CountDownLatch(1);
        List<Future<?>> futures = new ArrayList<>();
        for (int t = 0; t < threads; t++) {
            int thread = t;
            futures.add(pool.submit(() -> {
                start.await();
                for (int i = 0; i < ops; i++) {
                    action.accept(thread * ops + i);
                }
                return null;
            }));
        }
        long startNanos = System.nanoTime();
        start.countDown();
        for (Future<?> future : futures) {
            future.get(30, TimeUnit.SECONDS);
        }
        long wall = System.nanoTime() - startNanos;
        pool.shutdown();
        return wall;
    }

    private static void report(String scenario, long wallNanos, long throughputOps,
                               long expected, long actual) {
        double seconds = wallNanos / 1e9;
        System.out.printf("%-14s wall=%.3fs ops/s=%.0f expected=%d actual=%d %s%n",
                scenario, seconds, throughputOps / seconds, expected, actual,
                expected == actual ? "PASS" : "FAIL");
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
