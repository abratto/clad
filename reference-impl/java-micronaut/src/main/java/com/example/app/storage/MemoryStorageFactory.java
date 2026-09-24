package com.example.app.storage;

import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import io.micronaut.context.annotation.Factory;
import io.micronaut.context.annotation.Requires;
import jakarta.inject.Singleton;

/**
 * In-memory concept-state binding ({@link StorageBackend#MEMORY}).
 *
 * <p>Active unless {@code clad.storage=postgres}. This is the default: the
 * service runs with no database and no Docker — the same in-memory
 * {@code FactStore} the canonical profile uses. Concept state is transient
 * (discarded on restart), which is exactly right for dev, tests, and the
 * quick-start reading path.
 */
@Factory
@Requires(property = "clad.storage", notEquals = "postgres")
public final class MemoryStorageFactory {

    @Singleton
    public FactStore factStore() {
        return new InMemoryFactStore();
    }
}
