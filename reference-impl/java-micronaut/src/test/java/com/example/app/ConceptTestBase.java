package com.example.app;

import dev.legible.engine.FactStore;
import dev.legible.engine.InMemoryFactStore;
import org.junit.jupiter.api.BeforeEach;

import java.util.List;

/**
 * Shared fixtures for the concept tests. Uses the **in-memory** {@code FactStore}
 * so the concept suite runs without Docker; the same concepts also run against
 * Postgres under the flow/integration tests (clad.storage=postgres).
 *
 * <p>Concept actions are invoked directly via {@code Concept.execute}
 * (test-mode, no sync orchestration; that boundary belongs to 04e).
 */
public abstract class ConceptTestBase {

    protected static FactStore store;

    @BeforeEach
    void resetRegions() {
        if (store == null) {
            store = new InMemoryFactStore();
        }
        for (String concept : List.of("UserNaming", "PasswordAuth", "Session")) {
            for (var fact : store.region(concept).facts()) {
                store.region(concept).remove(fact.subject(), fact.predicate(), fact.value());
            }
        }
    }
}
