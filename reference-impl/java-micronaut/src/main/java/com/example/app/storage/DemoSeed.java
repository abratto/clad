package com.example.app.storage;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.usernaming.UserNamingConcept;
import dev.legible.engine.FactStore;
import io.micronaut.context.event.StartupEvent;
import io.micronaut.runtime.event.annotation.EventListener;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Seeds one demo user ({@code ada}) at startup, on whichever backend is
 * active. Backend-agnostic: it writes through the engine's {@code FactStore}
 * SPI, so the same seed works for in-memory and Postgres. Runs after any DDL
 * initialization (the Postgres {@code StoreInitializer} is ordered earlier as
 * the schema owner).
 */
@Singleton
public class DemoSeed {

    private final FactStore factStore;

    @Inject
    public DemoSeed(FactStore factStore) {
        this.factStore = factStore;
    }

    @EventListener
    void onStartup(StartupEvent event) {
        String userId = "ada00001-0000-0000-0000-000000000001";
        new UserNamingConcept(factStore.region("UserNaming")).seedUser(userId, "ada");
        new PasswordAuthConcept(factStore.region("PasswordAuth"))
                .seedCredential(userId, "correct-horse-battery-staple");
    }
}
