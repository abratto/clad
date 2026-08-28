package dev.legible.storage;

import dev.legible.engine.Fact;
import dev.legible.engine.FactStore;
import dev.legible.engine.Region;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * A {@link FactStore} backed by PostgreSQL tables derived via Halpin's
 * **Rmap**: one typed table per concept, one column per fact type, the
 * individual identifier as primary key, and {@code UNIQUE} constraints where
 * the fact model declares them.
 *
 * <p>The generic {@code Region} SPI ({@code predicate(subject) = value}) is
 * realised over the typed columns through a predicate→column mapping, so the
 * engine remains storage-agnostic while the schema stays deterministic and
 * correct. {@link PostgresFactStore} remains the lighter "fact realization"
 * alternative (a single generic {@code fact} relation).
 */
public final class RmapPostgresFactStore implements FactStore {

    private final DataSource dataSource;
    private final Map<String, RelationSchema> schemas;
    private final Map<String, Region> regions = new ConcurrentHashMap<>();

    public RmapPostgresFactStore(DataSource dataSource, List<RelationSchema> schemas) {
        this.dataSource = dataSource;
        this.schemas = new LinkedHashMap<>();
        for (RelationSchema schema : schemas) {
            this.schemas.put(schema.concept(), schema);
        }
    }

    /** Create every concept's table (idempotent). */
    public void createSchema() {
        for (RelationSchema schema : schemas.values()) {
            try (Connection c = dataSource.getConnection();
                 Statement st = c.createStatement()) {
                st.execute(schema.ddl());
            } catch (SQLException e) {
                throw new PostgresFactStore.UncheckedSQLException(e);
            }
        }
    }

    @Override
    public Region region(String concept) {
        RelationSchema schema = schemas.get(concept);
        if (schema == null) {
            throw new IllegalArgumentException(
                    "no Rmap schema for concept: " + concept);
        }
        return regions.computeIfAbsent(concept, c -> new RmapRegion(dataSource, schema));
    }

    private static final class RmapRegion implements Region {
        private final DataSource ds;
        private final RelationSchema schema;

        private RmapRegion(DataSource ds, RelationSchema schema) {
            this.ds = ds;
            this.schema = schema;
        }

        @Override
        public Set<String> read(String subject, String predicate) {
            RelationSchema.Column col = schema.columnFor(predicate);
            if (col == null) return Set.of();
            String sql = "SELECT " + col.column() + " FROM " + schema.table()
                    + " WHERE " + schema.idColumn() + " = ?";
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, subject);
                Set<String> out = new LinkedHashSet<>();
                try (ResultSet rs = ps.executeQuery()) {
                    if (rs.next() && rs.getString(1) != null) out.add(rs.getString(1));
                }
                return out;
            } catch (SQLException e) {
                throw new PostgresFactStore.UncheckedSQLException(e);
            }
        }

        @Override
        public void write(String subject, String predicate, String value) {
            RelationSchema.Column col = schema.columnFor(predicate);
            if (col == null) {
                throw new IllegalArgumentException(
                        "unknown predicate '" + predicate + "' for concept " + schema.concept());
            }
            String sql = "INSERT INTO " + schema.table() + " (" + schema.idColumn()
                    + ", " + col.column() + ") VALUES (?, ?) "
                    + "ON CONFLICT (" + schema.idColumn() + ") DO UPDATE SET "
                    + col.column() + " = EXCLUDED." + col.column();
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, subject);
                ps.setString(2, value);
                ps.executeUpdate();
            } catch (SQLException e) {
                throw new PostgresFactStore.UncheckedSQLException(e);
            }
        }

        @Override
        public void remove(String subject, String predicate, String value) {
            clear(subject, predicate);
        }

        @Override
        public void clear(String subject, String predicate) {
            RelationSchema.Column col = schema.columnFor(predicate);
            if (col == null) return;
            String sql = "UPDATE " + schema.table() + " SET " + col.column()
                    + " = NULL WHERE " + schema.idColumn() + " = ?";
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, subject);
                ps.executeUpdate();
            } catch (SQLException e) {
                throw new PostgresFactStore.UncheckedSQLException(e);
            }
        }

        @Override
        public Set<String> subjects(String predicate, String value) {
            RelationSchema.Column col = schema.columnFor(predicate);
            if (col == null) return Set.of();
            String sql = "SELECT " + schema.idColumn() + " FROM " + schema.table()
                    + " WHERE " + col.column() + " = ?";
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, value);
                Set<String> out = new LinkedHashSet<>();
                try (ResultSet rs = ps.executeQuery()) {
                    while (rs.next()) out.add(rs.getString(1));
                }
                return out;
            } catch (SQLException e) {
                throw new PostgresFactStore.UncheckedSQLException(e);
            }
        }

        @Override
        public List<Fact> facts() {
            String sql = "SELECT * FROM " + schema.table();
            try (Connection c = ds.getConnection();
                 PreparedStatement ps = c.prepareStatement(sql);
                 ResultSet rs = ps.executeQuery()) {
                List<Fact> out = new ArrayList<>();
                ResultSetMetaData meta = rs.getMetaData();
                while (rs.next()) {
                    String subject = rs.getString(schema.idColumn());
                    for (RelationSchema.Column col : schema.columns()) {
                        String value = rs.getString(col.column());
                        if (value != null) {
                            out.add(new Fact(subject, col.predicate(), value));
                        }
                    }
                }
                return out;
            } catch (SQLException e) {
                throw new PostgresFactStore.UncheckedSQLException(e);
            }
        }
    }
}
