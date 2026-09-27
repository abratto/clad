package dev.legible.storage;

import dev.legible.engine.Fact;
import dev.legible.engine.FactStore;
import dev.legible.engine.Region;
import org.jooq.DSLContext;
import org.jooq.Field;
import org.jooq.Record;
import org.jooq.Result;
import org.jooq.SQLDialect;
import org.jooq.Table;
import org.jooq.impl.DSL;

import javax.sql.DataSource;
import java.sql.SQLException;
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
 * individual identifier as primary key, {@code UNIQUE} where the fact model
 * declares it, and {@code DEFAULT} for cleared facts.
 *
 * <p><strong>jOOQ is the SQL interface.</strong> The tables are derived at
 * runtime from the concept state, so the queries are built with jOOQ's DSL over
 * dynamic {@code Table}/{@code Field} identifiers rather than generated classes
 * — no raw JDBC, no hand-written SQL for reads/writes. jOOQ owns connection and
 * dialect handling; {@link #createSchema()} still executes the Rmap DDL (kept
 * as the single source of the table shape, mirroring the Flyway base migration).
 *
 * <p>The generic {@code Region} SPI ({@code predicate(subject) = value}) is
 * realised over the typed columns through a predicate→column mapping, with
 * string↔typed value coercion driven by each column's Rmap-derived SQL type:
 * {@code INTEGER} values round-trip as decimal strings, {@code TIMESTAMP}
 * values round-trip as epoch-millisecond strings.
 */
public final class RmapPostgresFactStore implements FactStore {

    private final DSLContext dsl;
    private final Map<String, RelationSchema> schemas;
    private final Map<String, Region> regions = new ConcurrentHashMap<>();

    public RmapPostgresFactStore(DataSource dataSource, List<RelationSchema> schemas) {
        this.dsl = DSL.using(dataSource, SQLDialect.POSTGRES);
        this.schemas = new LinkedHashMap<>();
        for (RelationSchema schema : schemas) {
            this.schemas.put(schema.concept(), schema);
        }
    }

    /** Create every concept's table (idempotent). */
    public void createSchema() {
        try {
            for (RelationSchema schema : schemas.values()) {
                dsl.execute(schema.ddl());
            }
        } catch (org.jooq.exception.DataAccessException e) {
            throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
        }
    }

    @Override
    public Region region(String concept) {
        RelationSchema schema = schemas.get(concept);
        if (schema == null) {
            throw new IllegalArgumentException("no Rmap schema for concept: " + concept);
        }
        return regions.computeIfAbsent(concept, c -> new RmapRegion(dsl, schema));
    }

    private static final class RmapRegion implements Region {
        private final DSLContext dsl;
        private final RelationSchema schema;
        private final Table<?> table;
        private final Field<String> id;

        private RmapRegion(DSLContext dsl, RelationSchema schema) {
            this.dsl = dsl;
            this.schema = schema;
            this.table = DSL.table(DSL.name(schema.table()));
            this.id = DSL.field(DSL.name(schema.idColumn()), String.class);
        }

        @Override
        public Set<String> read(String subject, String predicate) {
            RelationSchema.Column col = schema.columnFor(predicate);
            if (col == null) return Set.of();
            Field<?> field = typedField(col);
            try {
                Record row = dsl.select(id, field).from(table)
                        .where(id.eq(subject)).fetchOne();
                if (row == null) return Set.of();
                Object value = row.get(field);
                if (value == null) return Set.of();
                return Set.of(toSpi(col, value));
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        @Override
        public void write(String subject, String predicate, String value) {
            RelationSchema.Column col = schema.columnFor(predicate);
            if (col == null) {
                throw new IllegalArgumentException(
                        "unknown predicate '" + predicate + "' for concept " + schema.concept());
            }
            Field<?> field = typedField(col);
            Object typed = fromSpi(col, value);
            Map<Field<?>, Object> insert = new LinkedHashMap<>();
            insert.put(id, subject);
            insert.put(field, typed);
            Map<Field<?>, Object> update = new LinkedHashMap<>();
            update.put(field, typed);
            try {
                dsl.insertInto(table).set(insert)
                        .onConflict(id).doUpdate().set(update)
                        .execute();
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
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
            // Clearing resets the fact to its declared DEFAULT if present,
            // otherwise to NULL (absent).
            Map<Field<?>, Object> set = new LinkedHashMap<>();
            set.put(typedField(col), col.defaultValue() != null
                    ? fromSpi(col, col.defaultValue()) : null);
            try {
                dsl.update(table).set(set).where(id.eq(subject)).execute();
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        @Override
        public Set<String> subjects(String predicate, String value) {
            RelationSchema.Column col = schema.columnFor(predicate);
            if (col == null) return Set.of();
            Field<Object> typed = typedObjectField(col);
            try {
                return new LinkedHashSet<>(
                        dsl.select(id).from(table)
                                .where(typed.eq(fromSpi(col, value)))
                                .fetch(id));
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        @Override
        public List<Fact> facts() {
            try {
                Result<Record> rows = dsl.select().from(table).fetch();
                List<Fact> out = new ArrayList<>();
                for (Record row : rows) {
                    String subject = row.get(id);
                    for (RelationSchema.Column col : schema.columns()) {
                        Object value = row.get(typedField(col));
                        if (value != null) {
                            out.add(new Fact(subject, col.predicate(), toSpi(col, value)));
                        }
                    }
                }
                return out;
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        private static Field<?> typedField(RelationSchema.Column col) {
            return switch (col.sqlType()) {
                case "INTEGER" -> DSL.field(DSL.name(col.column()), Integer.class);
                case "TIMESTAMP" -> DSL.field(DSL.name(col.column()), Timestamp.class);
                default -> DSL.field(DSL.name(col.column()), String.class);
            };
        }

        @SuppressWarnings("unchecked")
        private static Field<Object> typedObjectField(RelationSchema.Column col) {
            return (Field<Object>) typedField(col);
        }
    }

    /** Bind a string value using the column's Rmap-derived SQL type. */
    private static Object fromSpi(RelationSchema.Column col, String value) {
        return switch (col.sqlType()) {
            case "INTEGER" -> Integer.parseInt(value);
            case "TIMESTAMP" -> new Timestamp(Long.parseLong(value));
            default -> value;
        };
    }

    /** Read a typed value back to the SPI's string form. */
    private static String toSpi(RelationSchema.Column col, Object value) {
        return switch (col.sqlType()) {
            case "INTEGER" -> String.valueOf(value);
            case "TIMESTAMP" -> String.valueOf(((Timestamp) value).getTime());
            default -> String.valueOf(value);
        };
    }
}
