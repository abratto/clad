package com.example.app.storage.postgres;

import dev.legible.storage.RmapPostgresFactStore;
import io.micronaut.context.annotation.Requires;
import io.micronaut.context.event.StartupEvent;
import io.micronaut.runtime.event.annotation.EventListener;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.flywaydb.core.Flyway;

import javax.sql.DataSource;

/**
 * Applies base DDL at startup for the Postgres binding, in one deterministic
 * order:
 *
 * <ol>
 *   <li>Flyway owns the migration timeline ({{@code V1__login_rmap.sql}}
 *       documents the R-map base).</li>
 *   <li>{@link RmapPostgresFactStore#createSchema()} derives each concept's
 *       region table from the Stage 03b data models (idempotent, so tests may
 *       also call it directly).</li>
 * </ol>
 *
 * <p>Only present when {@code clad.storage=postgres}; the in-memory binding
 * needs no initialization. A demo seed is not applied here — the login flow's
 * happy path is seeded per environment (see the module README), keeping this
 * class to DDL ownership only.
 */
@Singleton
@Requires(property = "clad.storage", value = "postgres")
public class StoreInitializer {

    private final DataSource dataSource;
    private final RmapPostgresFactStore factStore;

    @Inject
    public StoreInitializer(DataSource dataSource, RmapPostgresFactStore factStore) {
        this.dataSource = dataSource;
        this.factStore = factStore;
    }

    @EventListener
    void onStartup(StartupEvent event) {
        Flyway.configure()
                .dataSource(dataSource)
                .load()
                .migrate();
        factStore.createSchema();
    }
}
