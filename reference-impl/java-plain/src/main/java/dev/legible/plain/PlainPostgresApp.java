package dev.legible.plain;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import dev.legible.engine.FactStore;
import dev.legible.example.login.LoginApp;
import dev.legible.storage.LoginSchemas;
import dev.legible.storage.RmapPostgresFactStore;
import org.flywaydb.core.Flyway;

import javax.sql.DataSource;

/**
 * The plain-Java durable profile: no transport framework at all. Boot order is
 * the whole contract — datasource, then Flyway (the schema owner; the runtime
 * store never creates tables), then the derived R-map store, then the app.
 *
 * <p>The login flows are the same {@link LoginApp} the micronaut profile runs
 * behind HTTP; here the transport is {@code main()} itself, which is the point:
 * an adopter swaps in Jetty, Spring, Ktor, or anything else without touching
 * engine, storage, or example concepts/syncs.
 *
 * <p>Concept state is acquired through a pooled {@link HikariDataSource}; the
 * pool is owned by the returned {@link Runtime} handle, so callers close it
 * deterministically (try-with-resources) instead of leaking connections.
 *
 * <p>Configuration, environment-style (defaults mirror
 * {@code java-micronaut/application.yml}): {@code DATABASE_URL} (default
 * {@code jdbc:postgresql://localhost:5432/clad}), {@code PGUSER} ({@code clad}),
 * {@code PGPASSWORD} ({@code clad}), {@code PGPOOL_MAX} ({@code 10}),
 * {@code PGPOOL_MIN_IDLE} ({@code 2}).
 */
public final class PlainPostgresApp {

    private PlainPostgresApp() {
    }

    public static void main(String[] args) {
        try (Runtime runtime = boot()) {
            LoginApp app = runtime.app();
            app.seedUser("ada", "correct-horse-battery-staple");
            System.out.println("login(ada, correct) -> "
                    + app.login("ada", "correct-horse-battery-staple"));
            System.out.println("login(ada, wrong)   -> " + app.login("ada", "nope"));
        }
    }

    /**
     * Boot the whole profile from the environment. The returned handle owns the
     * connection pool; close it when the application stops.
     */
    public static Runtime boot() {
        return boot(dataSourceUrl(),
                envOr("PGUSER", "clad"), envOr("PGPASSWORD", "clad"));
    }

    static Runtime boot(String url, String user, String password) {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(user);
        config.setPassword(password);
        config.setMaximumPoolSize(envInt("PGPOOL_MAX", 10));
        config.setMinimumIdle(envInt("PGPOOL_MIN_IDLE", 2));
        config.setConnectionTimeout(5_000);
        config.setPoolName("clad-plain");
        HikariDataSource dataSource = new HikariDataSource(config);
        try {
            Flyway.configure()
                    .dataSource(dataSource)
                    .load()
                    .migrate();

            FactStore facts = new RmapPostgresFactStore(dataSource, LoginSchemas.all());
            return new Runtime(dataSource, LoginApp.create(facts));
        } catch (RuntimeException e) {
            dataSource.close();
            throw e;
        }
    }

    private static String dataSourceUrl() {
        return envOr("DATABASE_URL", "jdbc:postgresql://localhost:5432/clad");
    }

    private static String envOr(String key, String fallback) {
        String value = System.getenv(key);
        return value == null || value.isBlank() ? fallback : value;
    }

    private static int envInt(String key, int fallback) {
        String value = System.getenv(key);
        if (value == null || value.isBlank()) {
            return fallback;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            return fallback;
        }
    }

    /**
     * The booted profile: the {@link LoginApp} plus the pooled {@link DataSource}
     * that backs it. Closing the handle closes the pool; it is idempotent.
     */
    public static final class Runtime implements AutoCloseable {

        private final HikariDataSource dataSource;
        private final LoginApp app;
        private boolean closed;

        private Runtime(HikariDataSource dataSource, LoginApp app) {
            this.dataSource = dataSource;
            this.app = app;
        }

        public LoginApp app() {
            return app;
        }

        public DataSource dataSource() {
            return dataSource;
        }

        @Override
        public synchronized void close() {
            if (closed) {
                return;
            }
            closed = true;
            dataSource.close();
        }
    }
}
