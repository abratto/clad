package com.example.app.storage.postgres;

import dev.legible.engine.FactStore;
import dev.legible.engine.SyncEngine;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;

import java.time.Instant;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The app concept's {@code lockedUntil} wire contract over the durable store,
 * driven through the real {@link SyncEngine} (so the region's
 * {@code TransactionalRegion} wrapper runs, as in production).
 *
 * <p>The {@code Region} SPI exchanges TIMESTAMP values as ISO-8601 instant
 * strings on both backends: a lock set by {@code PasswordAuthConcept} must read
 * back ISO-8601 (never raw epoch-millis digits), the lockout must still reject a
 * correct password within the window, and the typed column must hold a real
 * timestamp. The in-memory concept suite cannot catch an epoch/ISO mismatch
 * because no coercion happens there. Docker-backed and gated behind
 * {@code -Dclad.storage=postgres}.
 */
@EnabledIfSystemProperty(named = "clad.storage", matches = "postgres")
@MicronautTest
class PasswordAuthTimestampTest {

    // Seeded by DemoSeed at startup (ada).
    private static final String USERNAME = "ada";
    private static final String USER_ID = "ada00001-0000-0000-0000-000000000001";

    @Inject
    FactStore factStore;

    @Inject
    SyncEngine engine;

    @Test
    void lockedUntilIsAnIso8601InstantOnTheWireAndStillLocks() {
        // Five wrong attempts set the lock (threshold is 5).
        for (int i = 0; i < 5; i++) {
            engine.run("Web", "request", Map.of(
                    "route", "login", "username", USERNAME, "password", "wrong-" + i));
        }

        Set<String> locked = factStore.region("PasswordAuth").read(USER_ID, "lockedUntil");
        assertFalse(locked.isEmpty(), "the lock must be persisted after the threshold");

        String stored = locked.iterator().next();
        // Wire contract: ISO-8601 instants, never raw epoch-millis digits.
        Instant.parse(stored);
        assertTrue(stored.contains("T"), "the stored instant must be ISO-8601, was: " + stored);

        // The lock is honoured: a correct password within the window is refused.
        Map<String, Object> completion = engine.run("Web", "request", Map.of(
                "route", "login", "username", USERNAME,
                "password", "correct-horse-battery-staple"));
        assertEquals(401, completion.get("status"),
                "a locked account must refuse a correct password");
    }
}
