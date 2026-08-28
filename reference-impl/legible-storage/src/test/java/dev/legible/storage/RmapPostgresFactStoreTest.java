package dev.legible.storage;

import dev.legible.example.login.LoginApp;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The login feature runs against a relation-realized schema — Rmap-derived
 * typed tables, one per concept — rather than the generic fact relation.
 */
class RmapPostgresFactStoreTest {

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

    private RmapPostgresFactStore store;
    private LoginApp app;

    @BeforeEach
    void setUp() {
        resetTables();
        store = new RmapPostgresFactStore(dataSource, LoginSchemas.all());
        store.createSchema();
        app = LoginApp.create(store);
    }

    private void resetTables() {
        try (Connection c = dataSource.getConnection();
             Statement st = c.createStatement()) {
            for (String table : new String[]{"session", "passwordauth", "usernaming"}) {
                st.execute("DROP TABLE IF EXISTS " + table + " CASCADE");
            }
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Test
    void loginFlowRunsAgainstRmapSchema() {
        app.seedUser("alice", "secret");

        Map<String, Object> ok = app.login("alice", "secret");
        assertEquals(200, ok.get("status"));
        assertNotNull(ok.get("sessionToken"));

        Map<String, Object> wrong = app.login("alice", "wrong");
        assertEquals(401, wrong.get("status"));
        assertEquals("username or password didn't match", wrong.get("message"));

        Map<String, Object> unknown = app.login("nobody", "x");
        assertEquals(401, unknown.get("status"));

        for (int i = 0; i < 5; i++) {
            app.login("alice", "wrong");
        }
        Map<String, Object> locked = app.login("alice", "secret");
        assertEquals(401, locked.get("status"));
        assertEquals("Too many attempts. Try again in 15 minutes.", locked.get("message"));
    }

    @Test
    void schemaIsRmapDerived() throws Exception {
        // The schema is typed, per-concept tables with fact-type columns and
        // the individual identifier as primary key — not a generic fact table.
        try (Connection c = dataSource.getConnection();
             Statement st = c.createStatement()) {
            assertTrue(columnExists(st, "usernaming", "username"), "usernaming.username column");
            assertTrue(columnExists(st, "passwordauth", "failed_attempts"), "passwordauth.failed_attempts column");
            assertTrue(columnExists(st, "session", "opened_at"), "session.opened_at column");
        }
    }

    private static boolean columnExists(Statement st, String table, String column) throws Exception {
        String sql = "SELECT column_name FROM information_schema.columns "
                + "WHERE table_name = '" + table + "' AND column_name = '" + column + "'";
        try (ResultSet rs = st.executeQuery(sql)) {
            return rs.next();
        }
    }
}
