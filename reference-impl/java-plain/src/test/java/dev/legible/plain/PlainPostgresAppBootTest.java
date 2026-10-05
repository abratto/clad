package dev.legible.plain;

import dev.legible.example.login.LoginApp;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The plain profile boots the real stack: Flyway owns the schema, then
 * {@code RmapPostgresFactStore(LoginSchemas.all())} serves concept state, and
 * the login flows run end to end with no transport framework — the same path
 * {@link PlainPostgresApp#main} executes. Docker-backed and gated behind
 * {@code -Dclad.storage=postgres}.
 */
@EnabledIfSystemProperty(named = "clad.storage", matches = "postgres")
class PlainPostgresAppBootTest {

    private static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:16-alpine");

    private static PGSimpleDataSource dataSource;

    @BeforeAll
    static void startContainer() {
        POSTGRES.start();
        dataSource = new PGSimpleDataSource();
        dataSource.setUrl(POSTGRES.getJdbcUrl());
        dataSource.setUser(POSTGRES.getUsername());
        dataSource.setPassword(POSTGRES.getPassword());
    }

    @Test
    void bootRunsFlywayThenTheDerivedStoreAndTheFlowsWork() throws Exception {
        // The profile's own boot order: Flyway migrates first, then the
        // derived store and app are built on it. After boot, Flyway's history
        // must record the applied V1 (the schema's owner ran before the store).
        LoginApp app = PlainPostgresApp.boot(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());

        assertTrue(flywayAppliedV1(),
                "flyway_schema_history must record the applied V1 migration");

        app.seedUser("ada", "correct-horse-battery-staple");
        Map<String, Object> ok = app.login("ada", "correct-horse-battery-staple");
        assertEquals(200, ok.get("status"), ok.toString());
        assertNotNull(ok.get("sessionToken"), "the granted session is in the response");

        Map<String, Object> wrong = app.login("ada", "nope");
        assertEquals(401, wrong.get("status"));

        for (int i = 0; i < 5; i++) {
            app.login("ada", "wrong-" + i);
        }
        Map<String, Object> locked = app.login("ada", "correct-horse-battery-staple");
        assertEquals(401, locked.get("status"));
        assertEquals("Too many attempts. Try again in 15 minutes.", locked.get("message"));
    }

    /** True when Flyway's history table records an applied version 1. */
    private boolean flywayAppliedV1() throws Exception {
        try (Connection c = dataSource.getConnection();
             PreparedStatement ps = c.prepareStatement(
                     "SELECT count(*) FROM flyway_schema_history WHERE version = '1'");
             ResultSet rs = ps.executeQuery()) {
            rs.next();
            return rs.getInt(1) == 1;
        }
    }
}
