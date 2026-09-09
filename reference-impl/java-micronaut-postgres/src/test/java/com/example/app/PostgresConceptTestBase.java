package com.example.app;

import dev.legible.engine.FactStore;
import dev.legible.storage.LoginSchemas;
import dev.legible.storage.RmapPostgresFactStore;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.util.List;
import java.util.Map;

/**
 * Shared fixtures for the Postgres-backed concept tests: one Testcontainers
 * Postgres, one {@link RmapPostgresFactStore} whose schemas derive from the
 * Stage 03b data models ({@link LoginSchemas}).
 *
 * <p>Concept actions are invoked directly via {@code Concept.execute}
 * (test-mode, no sync orchestration; that boundary belongs to 04e).
 */
public abstract class PostgresConceptTestBase {

    private static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:16-alpine");

    protected static RmapPostgresFactStore store;

    @BeforeAll
    static void startDatabase() {
        POSTGRES.start();
        PGSimpleDataSource dataSource = new PGSimpleDataSource();
        dataSource.setUrl(POSTGRES.getJdbcUrl());
        dataSource.setUser(POSTGRES.getUsername());
        dataSource.setPassword(POSTGRES.getPassword());
        Flyway.configure().dataSource(dataSource).load().migrate();
        store = new RmapPostgresFactStore(dataSource, LoginSchemas.all());
        store.createSchema();
    }

    @BeforeEach
    void resetRegions() {
        for (String concept : List.of("UserNaming", "PasswordAuth", "Session")) {
            for (var fact : store.region(concept).facts()) {
                store.region(concept).remove(fact.subject(), fact.predicate(), fact.value());
            }
        }
    }
}
