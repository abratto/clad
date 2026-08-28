package dev.legible.storage;

import dev.legible.engine.Fact;
import dev.legible.engine.FactStore;
import dev.legible.engine.Region;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
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
 * individual identifier as primary key, {@code NOT NULL} for mandatory roles,
 * and {@code UNIQUE} constraints where the fact model declares them.
 *
 * <p>The generic {@code Region} SPI ({@code predicate(subject) = value}) is
 * realised over the typed columns through a predicate→column mapping, with
 * string↔typed value coercion driven by each column's Rmap-derived SQL type:
 * {@code INTEGER} values round-trip as decimal strings, {@code TIMESTAMP}
 * values round-trip as epoch-millisecond strings. The engine therefore stays
 * storage-agnostic while the relational schema is fully typed and correct.
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
                    if (rs.next()) {
                        String value = readColumn(rs, col);
                        if (value != null) out.add(value);
                    }
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
                setParam(ps, 2, col, value);
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
            // Clearing a fact resets it to its default if one is declared
            // (absent == default), otherwise it becomes absent (NULL).
            String sql = "UPDATE " + schema.table() + " SET " + col.column() + " = "
                    + (col.defaultValue() != null ? col.defaultValue() : "NULL")
                    + " WHERE " + schema.idColumn() + " = ?";
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
                setParam(ps, 1, col, value);
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
                while (rs.next()) {
                    String subject = rs.getString(schema.idColumn());
                    for (RelationSchema.Column col : schema.columns()) {
                        String value = readColumn(rs, col);
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

    /** Bind a string value using the column's Rmap-derived SQL type. */
    private static void setParam(PreparedStatement ps, int index,
                                 RelationSchema.Column col, String value) throws SQLException {
        switch (col.sqlType()) {
            case "INTEGER" -> ps.setInt(index, Integer.parseInt(value));
            case "TIMESTAMP" -> ps.setTimestamp(index, new Timestamp(Long.parseLong(value)));
            default -> ps.setString(index, value);
        }
    }

    /** Read a typed column back to the SPI's string form. */
    private static String readColumn(ResultSet rs, RelationSchema.Column col) throws SQLException {
        return switch (col.sqlType()) {
            case "INTEGER" -> {
                int v = rs.getInt(col.column());
                yield rs.wasNull() ? null : String.valueOf(v);
            }
            case "TIMESTAMP" -> {
                Timestamp ts = rs.getTimestamp(col.column());
                yield ts == null ? null : String.valueOf(ts.getTime());
            }
            default -> rs.getString(col.column());
        };
    }
}
