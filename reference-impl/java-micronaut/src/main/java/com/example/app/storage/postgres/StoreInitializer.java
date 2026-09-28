package com.example.app.storage.postgres;

import io.micronaut.context.annotation.Requires;
import io.micronaut.context.event.StartupEvent;
import io.micronaut.runtime.event.annotation.EventListener;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.flywaydb.core.Flyway;

import javax.sql.DataSource;

/**
 * Applies the schema at startup for the Postgres binding.
 *
 * <p><strong>Flyway owns DDL.</strong> The base migration
 * ({@code V1__login_rmap.sql}), generated from the Stage 03b R-map derivation,
 * is the single source of the table shape and its version history. The runtime
 * store does not create tables here —
 * {@link dev.legible.storage.RmapPostgresFactStore#createSchema()} remains only
 * as a dev/test helper (it applies the same derived DDL without Flyway).
 *
 * <p>Only present when {@code clad.storage=postgres}; the in-memory binding
 * needs no initialization. Demo data is not applied here — it is seeded by
 * {@code DemoSeed} through the engine's {@code FactStore} SPI, backend-agnostic
 * (see the module README).
 */
@Singleton
@Requires(property = "clad.storage", value = "postgres")
public class StoreInitializer {

    private final DataSource dataSource;

    @Inject
    public StoreInitializer(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @EventListener
    void onStartup(StartupEvent event) {
        Flyway.configure()
                .dataSource(dataSource)
                .load()
                .migrate();
    }
}
