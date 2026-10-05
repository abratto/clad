package dev.legible.plain;

import dev.legible.engine.FactStore;
import dev.legible.example.login.LoginApp;
import dev.legible.storage.LoginSchemas;
import dev.legible.storage.RmapPostgresFactStore;
import org.flywaydb.core.Flyway;

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
 * <p>Configuration, environment-style (defaults mirror
 * {@code java-micronaut/application.yml}): {@code DATABASE_URL} (default
 * {@code jdbc:postgresql://localhost:5432/clad}), {@code PGUSER} ({@code clad}),
 * {@code PGPASSWORD} ({@code clad}).
 */
public final class PlainPostgresApp {

    public static void main(String[] args) {
        LoginApp app = boot();
        app.seedUser("ada", "correct-horse-battery-staple");
        System.out.println("login(ada, correct) -> "
                + app.login("ada", "correct-horse-battery-staple"));
        System.out.println("login(ada, wrong)   -> " + app.login("ada", "nope"));
    }

    /**
     * Boot the whole profile from a {@link DataSource}-shaped configuration:
     * Flyway migration first, then the derived R-map store, then the app.
     */
    public static LoginApp boot() {
        return boot(dataSourceUrl(),
                envOr("PGUSER", "clad"), envOr("PGPASSWORD", "clad"));
    }

    static LoginApp boot(String url, String user, String password) {
        var dataSource = new org.postgresql.ds.PGSimpleDataSource();
        dataSource.setUrl(url);
        dataSource.setUser(user);
        dataSource.setPassword(password);

        Flyway.configure()
                .dataSource(dataSource)
                .load()
                .migrate();

        FactStore facts = new RmapPostgresFactStore(dataSource, LoginSchemas.all());
        return LoginApp.create(facts);
    }

    private static String dataSourceUrl() {
        return envOr("DATABASE_URL", "jdbc:postgresql://localhost:5432/clad");
    }

    private static String envOr(String key, String fallback) {
        String value = System.getenv(key);
        return value == null || value.isBlank() ? fallback : value;
    }
}
