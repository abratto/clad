package com.example.app.storage.postgres;

import dev.legible.engine.FactStore;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.jooq.DSLContext;
import org.jooq.SQLDialect;
import org.jooq.impl.DSL;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Set;

import static com.example.app.db.Tables.PASSWORD_AUTH;
import static com.example.app.db.Tables.USER_NAMING;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The durable Postgres persistence profile, end to end: Flyway applies the base
 * R-map migration, {@code StoreInitializer} derives the typed tables, and the
 * runtime state is readable/writable through <strong>jOOQ</strong> — the SQL
 * interface for the persistence stack (no raw JDBC, no Micronaut Data).
 *
 * <p>Docker-backed (Testcontainers) and therefore gated behind
 * {@code -Dclad.storage=postgres}; the default in-memory run skips it. It proves
 * the DDLDatabase-introspected jOOQ schema and the runtime {@code RmapDeriver}
 * DDL agree (a jOOQ write is visible to the engine's {@code FactStore}, and vice
 * versa), that R-map tables are typed with no cross-concept foreign keys, and
 * that Flyway owns the base schema.
 */
@EnabledIfSystemProperty(named = "clad.storage", matches = "postgres")
@MicronautTest
class RmapPostgresPersistenceTest {

    @Inject
    DataSource dataSource;

    @Inject
    FactStore factStore;

    private DSLContext dsl() {
        return DSL.using(dataSource, SQLDialect.POSTGRES);
    }

    @Test
    void flywayOwnsTheBaseSchema() throws Exception {
        try (Connection c = dataSource.getConnection();
             Statement st = c.createStatement();
             ResultSet rs = st.executeQuery(
                     "SELECT version, description FROM flyway_schema_history")) {
            boolean found = false;
            while (rs.next()) {
                if ("1".equals(rs.getString("version"))) {
                    found = true;
                    assertTrue(rs.getString("description").toLowerCase().contains("login"),
                            "V1 should be the login R-map base migration");
                }
            }
            assertTrue(found, "flyway_schema_history has no V1 migration");
        }
    }

    @Test
    void rmapTablesAreTypedWithNoCrossConceptForeignKey() throws Exception {
        try (Connection c = dataSource.getConnection();
             Statement st = c.createStatement()) {
            assertEquals("integer", columnType(st, "password_auth", "failed_attempts"));
            assertTrue(columnType(st, "session", "opened_at").contains("timestamp"),
                    "opened_at must be a timestamp");
            assertEquals("character varying", columnType(st, "user_naming", "username"));

            try (ResultSet rs = st.executeQuery(
                    "SELECT count(*) FROM information_schema.referential_constraints "
                            + "WHERE constraint_schema = current_schema()")) {
                assertTrue(rs.next());
                assertEquals(0, rs.getInt(1),
                        "an R-map schema must not carry cross-concept foreign keys (R2)");
            }
        }
    }

    @Test
    void jooqWriteIsVisibleToTheEngineStore() {
        // The generated jOOQ classes come from the Flyway migration
        // (DDLDatabase); the store derives its DDL from the concept state. A row
        // written through jOOQ must be the same row the engine reads — proving
        // the two agree, and that jOOQ is the SQL interface.
        dsl().insertInto(USER_NAMING)
                .columns(USER_NAMING.USER_ID, USER_NAMING.USERNAME)
                .values("u-jooq-1", "jooq-user")
                .execute();

        Set<String> username = factStore.region("UserNaming").read("u-jooq-1", "username");
        assertEquals(Set.of("jooq-user"), username);

        // ...and vice versa: the engine's write is readable as a typed jOOQ row.
        // Seed the mandatory credential column first. The SPI writes one fact at
        // a time; Rmap realises a mandatory role as NOT NULL, so an individual's
        // row must be created with its mandatory facts. This mirrors production
        // (the engine buffers an action's writes into one statement).
        factStore.region("PasswordAuth").write("u-jooq-1", "passwordHash", "sha256:seed");
        factStore.region("PasswordAuth").write("u-jooq-1", "failedAttempts", "3");
        Integer attempts = dsl().select(PASSWORD_AUTH.FAILED_ATTEMPTS)
                .from(PASSWORD_AUTH)
                .where(PASSWORD_AUTH.USER_ID.eq("u-jooq-1"))
                .fetchOne(PASSWORD_AUTH.FAILED_ATTEMPTS);
        assertNotNull(attempts);
        assertEquals(3, attempts);
    }

    private static String columnType(Statement st, String table, String column)
            throws Exception {
        try (PreparedStatement ps = st.getConnection().prepareStatement(
                "SELECT data_type FROM information_schema.columns "
                        + "WHERE table_name = ? AND column_name = ?")) {
            ps.setString(1, table);
            ps.setString(2, column);
            try (ResultSet rs = ps.executeQuery()) {
                assertTrue(rs.next(), "missing column " + table + "." + column);
                return rs.getString(1).toLowerCase();
            }
        }
    }
}
