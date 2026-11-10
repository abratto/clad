package dev.legible.storage;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import dev.legible.engine.Region;
import dev.legible.engine.TransactionalRegion;
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
import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
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
            String usernameType = columnType(st, "user_naming", "username");
            assertTrue(usernameType.startsWith("TEXT")
                            || usernameType.startsWith("CHARACTER VARYING"),
                    "text is realised as TEXT or varchar: " + usernameType);
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

    @Test
    void optionalPredicateReadsEmptyUntilTheLockIsSet() throws Exception {
        // `lockedUntil` is optional on PasswordAuth. The negative state pattern
        // (`absent`) is resolved by `Region.read` returning empty, so the typed
        // R-map store must return empty while no lock is set — not a
        // NULL-valued fact — and a value once the flow sets one.
        app.seedUser("alice", "secret");
        String userId = queryOne("SELECT user_id FROM password_auth LIMIT 1");
        Region passwordAuth = store.region("PasswordAuth");

        assertTrue(passwordAuth.read(userId, "lockedUntil").isEmpty(),
                "before lockout, lockedUntil is absent (reads empty)");

        for (int i = 0; i < 5; i++) {
            app.login("alice", "wrong");
        }
        assertFalse(passwordAuth.read(userId, "lockedUntil").isEmpty(),
                "after lockout, lockedUntil is present");
    }

    @Test
    void writingOneFactUpdatesAnExistingRowWithoutViolatingNotNull() throws Exception {
        // The SPI writes one fact at a time. Updating a single column of an
        // existing individual must update in place, not attempt an upsert whose
        // proposed insert tuple fails NOT NULL on the absent mandatory sibling
        // (PostgreSQL validates NOT NULL before resolving ON CONFLICT). This is
        // the write path a caller uses outside an engine action (no
        // TransactionalRegion buffer).
        app.seedUser("alice", "secret");
        String userId = queryOne("SELECT user_id FROM password_auth LIMIT 1");
        Region passwordAuth = store.region("PasswordAuth");

        passwordAuth.write(userId, "failedAttempts", "4");
        assertEquals("4", passwordAuth.read(userId, "failedAttempts").iterator().next(),
                "the fact must update the existing row");
        passwordAuth.write(userId, "failedAttempts", "7");
        assertEquals("7", passwordAuth.read(userId, "failedAttempts").iterator().next(),
                "a second write must overwrite in place");
        // The mandatory credential is untouched by the partial writes.
        assertFalse(passwordAuth.read(userId, "passwordHash").isEmpty());
    }

    @Test
    void aLoneWriteToAnUnknownIndividualSurfacesTheMissingMandatoryFact() {
        // No row exists and `passwordHash` is mandatory (NOT NULL, no default):
        // a lone optional write cannot create the individual, so the insert must
        // fail loudly rather than invent a value.
        Region passwordAuth = store.region("PasswordAuth");
        assertThrows(PostgresFactStore.UncheckedSQLException.class,
                () -> passwordAuth.write("nobody", "failedAttempts", "1"),
                "an incomplete mandatory row must be rejected, not fabricated");
    }

    @Test
    void aConceptActionFlushCommitsOrRollsBackAsOneUnit() {
        // Two buffered writes in one action: the first is valid, the second
        // duplicates the username UNIQUE constraint. The flush is one
        // transaction, so the first row must not survive the failed action.
        TransactionalRegion userNaming = (TransactionalRegion) store.region("UserNaming");
        userNaming.beginAction();
        userNaming.write("atomic-1", "username", "atomic-alice");
        userNaming.write("atomic-2", "username", "atomic-alice");

        assertThrows(PostgresFactStore.UncheckedSQLException.class, userNaming::flushAction,
                "the duplicate username must fail the flush");

        assertTrue(userNaming.read("atomic-1", "username").isEmpty(),
                "the first row must roll back with the failed action");
        assertTrue(userNaming.read("atomic-2", "username").isEmpty(),
                "the duplicate row must not be written");
    }

    @Test
    void storeRunsOnAHikariPool() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(POSTGRES.getJdbcUrl());
        config.setUsername(POSTGRES.getUsername());
        config.setPassword(POSTGRES.getPassword());
        config.setMaximumPoolSize(4);
        try (HikariDataSource pooled = new HikariDataSource(config)) {
            RmapPostgresFactStore hikariStore =
                    new RmapPostgresFactStore(pooled, LoginSchemas.all());
            LoginApp app = LoginApp.create(hikariStore);
            app.seedUser("hikari-user", "secret");
            Map<String, Object> ok = app.login("hikari-user", "secret");
            assertEquals(200, ok.get("status"), ok.toString());
        }
    }

    @Test
    void concurrentActionsOnDifferentSubjectsKeepSeparateBuffers() throws Exception {
        Region region = store.region("UserNaming");
        ExecutorService pool = Executors.newFixedThreadPool(2);
        CountDownLatch start = new CountDownLatch(1);

        Callable<Void> first = () -> {
            start.await();
            TransactionalRegion tx = (TransactionalRegion) region;
            tx.beginAction();
            region.write("cb-1", "username", "cb-1");
            Thread.sleep(10);
            tx.flushAction();
            return null;
        };
        Callable<Void> second = () -> {
            start.await();
            TransactionalRegion tx = (TransactionalRegion) region;
            tx.beginAction();
            region.write("cb-2", "username", "cb-2");
            Thread.sleep(10);
            tx.flushAction();
            return null;
        };

        Future<Void> f1 = pool.submit(first);
        Future<Void> secondFuture = pool.submit(second);
        start.countDown();
        f1.get(5, TimeUnit.SECONDS);
        secondFuture.get(5, TimeUnit.SECONDS);
        pool.shutdown();

        assertEquals(Set.of("cb-1"), region.read("cb-1", "username"));
        assertEquals(Set.of("cb-2"), region.read("cb-2", "username"));
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
