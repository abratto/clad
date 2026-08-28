package dev.legible.storage;

import dev.legible.engine.Fact;
import dev.legible.engine.FactStore;
import dev.legible.engine.Region;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * A {@link FactStore} backed by a PostgreSQL {@code fact} relation. Facts are
 * rows {@code (concept, subject, predicate, value)}; the {@code concept} column
 * is the named persistence region (R2 — one region per concept).
 *
 * <p>This is the relational profile implementation of the fire-after-commit
 * engine's storage SPI — the same {@code Concept}/{@code SyncRule} code runs
 * against it unmodified.
 */
public final class PostgresFactStore implements FactStore {

    /** DDL for the backing relation. Executed once at schema setup. */
    public static final String SCHEMA = """
            CREATE TABLE IF NOT EXISTS fact (
              concept   TEXT NOT NULL,
              subject   TEXT NOT NULL,
              predicate TEXT NOT NULL,
              value     TEXT NOT NULL,
              PRIMARY KEY (concept, subject, predicate, value)
            )
            """;

    private final DataSource dataSource;
    private final Map<String, Region> regions = new ConcurrentHashMap<>();

    public PostgresFactStore(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public Region region(String concept) {
        return regions.computeIfAbsent(concept, c -> new PgRegion(dataSource, c));
    }

    private static final class PgRegion implements Region {
        private final DataSource ds;
        private final String concept;

        private PgRegion(DataSource ds, String concept) {
            this.ds = ds;
            this.concept = concept;
        }

        @Override
        public Set<String> read(String subject, String predicate) {
            String sql = "SELECT value FROM fact WHERE concept = ? AND subject = ? AND predicate = ?";
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, concept);
                ps.setString(2, subject);
                ps.setString(3, predicate);
                Set<String> out = new LinkedHashSet<>();
                try (ResultSet rs = ps.executeQuery()) {
                    while (rs.next()) out.add(rs.getString(1));
                }
                return out;
            } catch (SQLException e) {
                throw new UncheckedSQLException(e);
            }
        }

        @Override
        public void write(String subject, String predicate, String value) {
            exec("INSERT INTO fact (concept, subject, predicate, value) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING",
                    concept, subject, predicate, value);
        }

        @Override
        public void remove(String subject, String predicate, String value) {
            exec("DELETE FROM fact WHERE concept = ? AND subject = ? AND predicate = ? AND value = ?",
                    concept, subject, predicate, value);
        }

        @Override
        public void clear(String subject, String predicate) {
            exec("DELETE FROM fact WHERE concept = ? AND subject = ? AND predicate = ?",
                    concept, subject, predicate);
        }

        @Override
        public Set<String> subjects(String predicate, String value) {
            String sql = "SELECT subject FROM fact WHERE concept = ? AND predicate = ? AND value = ?";
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, concept);
                ps.setString(2, predicate);
                ps.setString(3, value);
                Set<String> out = new LinkedHashSet<>();
                try (ResultSet rs = ps.executeQuery()) {
                    while (rs.next()) out.add(rs.getString(1));
                }
                return out;
            } catch (SQLException e) {
                throw new UncheckedSQLException(e);
            }
        }

        @Override
        public List<Fact> facts() {
            String sql = "SELECT subject, predicate, value FROM fact WHERE concept = ?";
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, concept);
                List<Fact> out = new ArrayList<>();
                try (ResultSet rs = ps.executeQuery()) {
                    while (rs.next()) {
                        out.add(new Fact(rs.getString(1), rs.getString(2), rs.getString(3)));
                    }
                }
                return out;
            } catch (SQLException e) {
                throw new UncheckedSQLException(e);
            }
        }

        private void exec(String sql, String... params) {
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                for (int i = 0; i < params.length; i++) {
                    ps.setString(i + 1, params[i]);
                }
                ps.executeUpdate();
            } catch (SQLException e) {
                throw new UncheckedSQLException(e);
            }
        }
    }

    /** Runtime wrapper so callers don't have to handle checked {@link SQLException}. */
    public static final class UncheckedSQLException extends RuntimeException {
        public UncheckedSQLException(SQLException cause) {
            super(cause);
        }
    }
}
