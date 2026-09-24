package com.example.app.storage.postgres;

import dev.legible.storage.LoginSchemas;
import dev.legible.storage.RmapPostgresFactStore;
import io.micronaut.context.annotation.Factory;
import io.micronaut.context.annotation.Primary;
import io.micronaut.context.annotation.Requires;
import jakarta.inject.Singleton;

import javax.sql.DataSource;

/**
 * Postgres concept-state binding ({@link com.example.app.storage.StorageBackend#POSTGRES}).
 *
 * <p>Active when {@code clad.storage=postgres}. Concept state lives in
 * R-map-derived typed tables (Stage 03b data models) via
 * {@link RmapPostgresFactStore}. The action log stays in-memory in every
 * binding — only concept state differs (see `legible-storage/`).
 *
 * <p>{@code @Primary} so the engine's {@code FactStore} injection resolves to
 * this store when the Postgres binding is active (the in-memory factory is not
 * present in that case).
 */
@Factory
@Requires(property = "clad.storage", value = "postgres")
public final class PostgresStorageFactory {

    @Singleton
    @Primary
    public RmapPostgresFactStore factStore(DataSource dataSource) {
        return new RmapPostgresFactStore(dataSource, LoginSchemas.all());
    }
}
