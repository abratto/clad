package dev.legible.storage;

import dev.legible.example.login.LoginApp;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.PreparedStatement;
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
            for (String table : new String[]{"session", "password_auth", "user_naming"}) {
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
    void schemaIsRmapDerivedWithFullTyping() throws Exception {
        // The schema is typed, per-concept tables with fact-type columns, the
        // individual identifier as primary key, DEFAULT for resettable facts,
        // and UNIQUE from the fact model — not a generic fact table.
        try (Connection c = dataSource.getConnection();
             Statement st = c.createStatement()) {
            assertEquals("TEXT", columnType(st, "user_naming", "username"));
            assertEquals("INTEGER", columnType(st, "password_auth", "failed_attempts"));
            assertTrue(columnType(st, "password_auth", "locked_until").startsWith("TIMESTAMP"));
            assertTrue(columnType(st, "session", "opened_at").startsWith("TIMESTAMP"));
            assertEquals("0", columnDefault(st, "password_auth", "failed_attempts"));
        }
    }

    @Test
    void typedValuesRoundTripThroughTheSpi() {
        // The lockout flow exercises INTEGER (failed_attempts) and TIMESTAMP
        // (locked_until) coercion: 5 wrong passwords increment the counter and
        // set a lock, then a correct password is rejected as LOCKED.
        app.seedUser("alice", "secret");
        for (int i = 0; i < 5; i++) {
            app.login("alice", "wrong");
        }
        assertEquals(401, app.login("alice", "secret").get("status"));
        assertEquals("Too many attempts. Try again in 15 minutes.",
                app.login("alice", "secret").get("message"));
    }

    @Test
    void persistedConceptStateIsCorrect() throws Exception {
        app.seedUser("alice", "secret");
        Map<String, Object> ok = app.login("alice", "secret");
        assertEquals(200, ok.get("status"));
        String sessionToken = (String) ok.get("sessionToken");

        // UserNaming stored the username -> opaque userId.
        String userId = queryOne("SELECT user_id FROM user_naming WHERE username = 'alice'");
        assertNotNull(userId, "UserNaming must persist the opaque userId");

        // PasswordAuth stored a credential for that same userId.
        String hash = queryOne("SELECT password_hash FROM password_auth WHERE user_id = ?", userId);
        assertNotNull(hash, "PasswordAuth must persist the credential");
        assertTrue(hash.startsWith("sha256:"));

        // Session stored the granted session keyed to the userId; the token
        // round-trips back to the user it belongs to.
        String sessionUserId = queryOne("SELECT user_id FROM session WHERE session_id = ?", sessionToken);
        assertEquals(userId, sessionUserId, "the session must be related to the correct user");

        // Drive lockout: the counter and lock are persisted as typed values.
        for (int i = 0; i < 5; i++) {
            app.login("alice", "wrong");
        }
        assertEquals("5", queryOne("SELECT failed_attempts FROM password_auth WHERE user_id = ?", userId),
                "failed_attempts must be persisted as the typed integer 5");
        assertNotNull(queryOne("SELECT locked_until FROM password_auth WHERE user_id = ?", userId),
                "locked_until must be persisted as a timestamp");
    }

    private String queryOne(String sql, String... params) throws Exception {
        try (Connection c = dataSource.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {
            for (int i = 0; i < params.length; i++) {
                ps.setString(i + 1, params[i]);
            }
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getString(1) : null;
            }
        }
    }

    private static boolean columnExists(Statement st, String table, String column) throws Exception {
        String sql = "SELECT column_name FROM information_schema.columns "
                + "WHERE table_name = '" + table + "' AND column_name = '" + column + "'";
        try (ResultSet rs = st.executeQuery(sql)) {
            return rs.next();
        }
    }

    private static String columnType(Statement st, String table, String column) throws Exception {
        String sql = "SELECT data_type FROM information_schema.columns "
                + "WHERE table_name = '" + table + "' AND column_name = '" + column + "'";
        try (ResultSet rs = st.executeQuery(sql)) {
            assertTrue(rs.next(), "missing column " + table + "." + column);
            return rs.getString(1).toUpperCase();
        }
    }

    private static String columnDefault(Statement st, String table, String column) throws Exception {
        String sql = "SELECT column_default FROM information_schema.columns "
                + "WHERE table_name = '" + table + "' AND column_name = '" + column + "'";
        try (ResultSet rs = st.executeQuery(sql)) {
            assertTrue(rs.next(), "missing column " + table + "." + column);
            String d = rs.getString(1);
            return d == null ? null : d.replaceAll("\\D", "");
        }
    }
}
