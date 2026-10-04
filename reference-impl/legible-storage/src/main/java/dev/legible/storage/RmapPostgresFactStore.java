package dev.legible.storage;

import dev.legible.engine.Fact;
import dev.legible.engine.FactStore;
import dev.legible.engine.Region;
import dev.legible.engine.TransactionalRegion;
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
 * A {@link FactStore} backed by a PostgreSQL R-map schema — one concept region
 * per concept (R2), realised as a <strong>table set</strong> ({@link RmapModel}).
 *
 * <p>Each fact {@code predicate(subject) = value} is routed to the table that
 * realises the predicate, and the typed column is read/written through a
 * predicate→column mapping with string↔typed value coercion.
 * {@code INTEGER} values round-trip as decimal strings; {@code TIMESTAMP}
 * values as ISO-8601 instant strings.
 *
 * <p><strong>Transactional writes.</strong> The region implements
 * {@link TransactionalRegion}: writes during one concept action are buffered and
 * flushed as at-most-one multi-column statement per row, which is what lets
 * mandatory columns be {@code NOT NULL}. Retracts are buffered too, so an
 * action's remove-then-write coalesces to the final value and a retract never
 * resurrects a stored row bare. Multi-valued facts (a predicate written with
 * several values) live in their own child table and are flushed as rows.
 *
 * <p><strong>DDL is Flyway's.</strong> This store does not create tables at
 * runtime in a deployed R-map profile ({@link #createSchema()} is a dev/test
 * helper applying the same derived DDL).
 */
public final class RmapPostgresFactStore implements FactStore {

    private final DataSource dataSource;
    private final DSLContext dsl;
    private final Map<String, RmapModel> models = new LinkedHashMap<>();
    private final Map<String, Region> regions = new ConcurrentHashMap<>();

    public RmapPostgresFactStore(DataSource dataSource, List<RelationSchema> schemas) {
        this.dataSource = dataSource;
        this.dsl = DSL.using(dataSource, SQLDialect.POSTGRES);
        // Group single-table schemas by concept; a concept may also be supplied
        // as several tables directly.
        Map<String, List<RelationSchema>> byConcept = new LinkedHashMap<>();
        for (RelationSchema schema : schemas) {
            byConcept.computeIfAbsent(schema.concept(), k -> new ArrayList<>()).add(schema);
        }
        for (Map.Entry<String, List<RelationSchema>> e : byConcept.entrySet()) {
            models.put(e.getKey(), new RmapModel(e.getKey(), e.getValue()));
        }
    }

    /** Construct from derived models (multi-table regions). */
    public RmapPostgresFactStore(DataSource dataSource, RmapModel model) {
        this(dataSource, model.tables());
    }

    /**
     * Create every table (idempotent).
     *
     * <p><strong>Dev/test helper only.</strong> When a SQL/R-map store is
     * deployed, Flyway owns DDL: the schema is a generated, versioned migration
     * ({@link RmapMigration}), applied at startup, not created by the runtime
     * store. This method applies the same derived DDL directly, for tests and
     * local use without Flyway.
     */
    public void createSchema() {
        try {
            for (RmapModel model : models.values()) {
                for (RelationSchema schema : model.tables()) {
                    dsl.execute(schema.ddl());
                }
            }
        } catch (org.jooq.exception.DataAccessException e) {
            throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
        }
    }

    @Override
    public Region region(String concept) {
        RmapModel model = models.get(concept);
        if (model == null) {
            throw new IllegalArgumentException("no Rmap schema for concept: " + concept);
        }
        return regions.computeIfAbsent(concept, c -> new RmapRegion(dsl, model));
    }

    @Override
    public Region maybeRegion(String concept) {
        RmapModel model = models.get(concept);
        return model == null ? null : regions.computeIfAbsent(concept, c -> new RmapRegion(dsl, model));
    }

    /**
     * One concept's region, realised over its table set. Routes each fact to the
     * table that owns its predicate.
     */
    private static final class RmapRegion implements TransactionalRegion {
        private final DSLContext dsl;
        private final RmapModel model;

        // Buffered writes for the current action: subject -> table -> column -> value.
        // A buffered retract is the {@link #RETRACTED} marker; a multi-valued
        // (child-table) fact accumulates a list of values per column.
        private final Map<String, Map<String, Map<String, Object>>> buffer = new LinkedHashMap<>();
        private boolean buffering = false;

        private RmapRegion(DSLContext dsl, RmapModel model) {
            this.dsl = dsl;
            this.model = model;
        }

        // ---- reads ----------------------------------------------------------

        @Override
        public Set<String> read(String subject, String predicate) {
            RelationSchema schema = model.tableForPredicate(predicate);
            if (schema == null) {
                return Set.of();
            }
            RelationSchema.Column col = schema.columnFor(predicate);
            try {
                Field<?> field = typedField(col);
                Field<String> subjectCol = subjectField(schema);
                List<?> rows = dsl.select(field).from(table(schema))
                        .where(subjectCol.eq(subject)).fetch(field);
                Set<String> out = new LinkedHashSet<>();
                for (Object raw : rows) {
                    if (raw != null) {
                        out.add(toSpi(col, raw));
                    }
                }
                return out;
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        @Override
        public Set<String> subjects(String predicate, String value) {
            RelationSchema schema = model.tableForPredicate(predicate);
            if (schema == null) {
                return Set.of();
            }
            RelationSchema.Column col = schema.columnFor(predicate);
            try {
                Field<String> subjectCol = subjectField(schema);
                Field<Object> typed = typedObjectField(col);
                return new LinkedHashSet<>(dsl.select(subjectCol).from(table(schema))
                        .where(typed.eq(fromSpi(col, value))).fetch(subjectCol));
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        @Override
        public List<Fact> facts() {
            List<Fact> out = new ArrayList<>();
            for (RelationSchema schema : model.tables()) {
                try {
                    Result<Record> rows = dsl.select().from(table(schema)).fetch();
                    for (Record row : rows) {
                        // Identity columns carry the individual's key components
                        // (joined into the subject); data columns carry its
                        // facts. A child table's value column is data even
                        // though it sits inside the composite PK.
                        List<String> keyParts = new ArrayList<>();
                        boolean complete = true;
                        for (RelationSchema.Column idCol : schema.identityColumns()) {
                            Object v = row.get(DSL.field(DSL.name(idCol.column()), String.class));
                            if (v == null) {
                                complete = false;
                                break;
                            }
                            keyParts.add(String.valueOf(v));
                        }
                        if (!complete) {
                            continue;
                        }
                        String subject = Region.join(keyParts);
                        for (RelationSchema.Column col : schema.dataColumns()) {
                            Object value = row.get(typedField(col));
                            if (value != null) {
                                out.add(new Fact(subject, col.predicate(), toSpi(col, value)));
                            }
                        }
                    }
                } catch (org.jooq.exception.DataAccessException e) {
                    throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
                }
            }
            return out;
        }

        // ---- transactional writes ------------------------------------------

        @Override
        public void beginAction() {
            buffer.clear();
            buffering = true;
        }

        @Override
        public void flushAction() {
            buffering = false;
            for (Map.Entry<String, Map<String, Map<String, Object>>> bySubject : buffer.entrySet()) {
                flushSubject(bySubject.getKey(), bySubject.getValue());
            }
            buffer.clear();
        }

        @Override
        public void abortAction() {
            buffering = false;
            buffer.clear();
        }

        @Override
        public void write(String subject, String predicate, String value) {
            RelationSchema schema = model.tableForPredicate(predicate);
            if (schema == null) {
                throw new IllegalArgumentException(
                        "unknown predicate '" + predicate + "' for concept " + model.concept());
            }
            RelationSchema.Column col = schema.columnFor(predicate);
            if (buffering) {
                appendBuffered(schema, subject, Map.ofEntries(
                        Map.entry(col.column(), fromSpi(col, value))),
                        schema.primaryKey().contains(col.column()));
                return;
            }
            writeColumn(schema, col, subject, fromSpi(col, value));
        }

        // ---- composite-subject forms ---------------------------------------

        @Override
        public Set<String> read(List<String> subject, String predicate) {
            RelationSchema schema = model.tableForPredicate(predicate);
            if (schema == null || schema.primaryKey().size() != subject.size()) {
                return read(Region.join(subject), predicate);
            }
            RelationSchema.Column col = schema.columnFor(predicate);
            Field<?> field = typedField(col);
            try {
                var cond = compositeCondition(schema, subject);
                Result<?> rows = dsl.select(field).from(table(schema)).where(cond).fetch();
                Set<String> out = new LinkedHashSet<>();
                for (Object raw : rows.getValues(field)) {
                    if (raw != null) {
                        out.add(toSpi(col, raw));
                    }
                }
                return out;
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        @Override
        public void write(List<String> subject, String predicate, String value) {
            RelationSchema schema = model.tableForPredicate(predicate);
            if (schema == null || schema.primaryKey().size() != subject.size()) {
                write(Region.join(subject), predicate, value);
                return;
            }
            RelationSchema.Column col = schema.columnFor(predicate);
            Object typed = fromSpi(col, value);
            Map<String, Object> colsByName = new LinkedHashMap<>();
            List<String> pk = schema.primaryKey();
            for (int i = 0; i < pk.size(); i++) {
                colsByName.put(pk.get(i), subject.get(i));
            }
            colsByName.put(col.column(), typed);
            if (buffering) {
                appendBuffered(schema, Region.join(subject), colsByName, false);
                return;
            }
            try {
                var cond = compositeCondition(schema, subject);
                if (dsl.fetchCount(table(schema), cond) > 0) {
                    Map<Field<?>, Object> set = new LinkedHashMap<>();
                    set.put(DSL.field(DSL.name(col.column())), typed);
                    dsl.update(table(schema)).set(set).where(cond).execute();
                } else {
                    Map<Field<?>, Object> cols = new LinkedHashMap<>();
                    for (Map.Entry<String, Object> e : colsByName.entrySet()) {
                        cols.put(DSL.field(DSL.name(e.getKey())), e.getValue());
                    }
                    dsl.insertInto(table(schema)).set(cols).execute();
                }
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        @Override
        public void remove(List<String> subject, String predicate, String value) {
            clear(subject, predicate);
        }

        @Override
        public void clear(List<String> subject, String predicate) {
            RelationSchema schema = model.tableForPredicate(predicate);
            if (schema == null || schema.primaryKey().size() != subject.size()) {
                clear(Region.join(subject), predicate);
                return;
            }
            RelationSchema.Column col = schema.columnFor(predicate);
            if (bufferRetract(schema, subject, col, null)) {
                return;
            }
            applyRetract(schema, col, compositeCondition(schema, subject),
                    DSL.field(DSL.name(col.column())));
        }

        private org.jooq.Condition compositeCondition(RelationSchema schema, List<String> subject) {
            org.jooq.Condition cond = null;
            List<String> pk = schema.primaryKey();
            for (int i = 0; i < pk.size(); i++) {
                org.jooq.Condition c = DSL.field(DSL.name(pk.get(i)), String.class).eq(subject.get(i));
                cond = (cond == null) ? c : cond.and(c);
            }
            return cond;
        }

        // ---- transactional buffer -------------------------------------------

        /** A buffered retract marker for one stored column of one individual. */
        private static final Object RETRACTED = new Object() {
            @Override public String toString() { return "<retracted>"; }
        };

        /**
         * When this action is buffered (a concept action's read-modify-write),
         * a retract of one of the region's stored facts must not touch the
         * database immediately: writing a value then retracting an old one in
         * one action coalesces at flush to the final value, and a retract
         * without a following write clears the stored value to its Rmap
         * default at flush time — never deleting the row the individual's
         * other stored columns live in. A buffered write of the same column
         * overwrites the marker, which is the coalescing.
         */
        private boolean bufferRetract(RelationSchema schema, List<String> compositeSubject,
                                      RelationSchema.Column col, String subject) {
            if (!buffering) {
                return false;
            }
            String key = compositeSubject != null ? Region.join(compositeSubject) : subject;
            Map<String, Object> draft = buffer
                    .computeIfAbsent(key, k -> new LinkedHashMap<>())
                    .computeIfAbsent(schema.qualifiedName(), k -> new LinkedHashMap<>());
            draft.put(col.column(), RETRACTED);
            return true;
        }

        /**
         * Buffer one write row-draft. {@code valueColumnAccumulates} marks a
         * multi-valued (child-table) fact column: repeated writes of that
         * column for the same individual within one action accumulate as a
         * list (one row per value at flush); every other column's later write
         * overwrites its earlier one.
         */
        private void appendBuffered(RelationSchema schema, String subject,
                                    Map<String, Object> columnsByName,
                                    boolean valueColumnAccumulates) {
            Map<String, Object> cols = buffer
                    .computeIfAbsent(subject, k -> new LinkedHashMap<>())
                    .computeIfAbsent(schema.qualifiedName(), k -> new LinkedHashMap<>());
            for (Map.Entry<String, Object> e : columnsByName.entrySet()) {
                if (valueColumnAccumulates && cols.containsKey(e.getKey())
                        && cols.get(e.getKey()) instanceof List<?> list) {
                    List<Object> merged = new ArrayList<Object>(list);
                    merged.add(e.getValue());
                    cols.put(e.getKey(), merged);
                } else if (valueColumnAccumulates && cols.get(e.getKey()) != null) {
                    cols.put(e.getKey(), new ArrayList<Object>(
                            List.of(cols.get(e.getKey()), e.getValue())));
                } else {
                    cols.put(e.getKey(), e.getValue());
                }
            }
        }

        /** The column's cleared value: its default when resettable, else none. */
        private static Object clearedValue(RelationSchema.Column col) {
            return col.defaultValue() != null ? fromSpi(col, col.defaultValue()) : null;
        }

        /**
         * Immediate (unbuffered) retract: a key component or a mandatory fact
         * without a default realises a row's identity/existence, so the row is
         * removed; anything else resets to the Rmap default (or SQL NULL).
         */
        private void applyRetract(RelationSchema schema, RelationSchema.Column col,
                                  org.jooq.Condition where, org.jooq.Field<?> columnField) {
            try {
                if (isKeyColumn(schema, col) || (col.mandatory() && clearedValue(col) == null)) {
                    dsl.deleteFrom(table(schema)).where(where).execute();
                    return;
                }
                Map<Field<?>, Object> set = new LinkedHashMap<>();
                set.put(columnField, clearedValue(col));
                dsl.update(table(schema)).set(set).where(where).execute();
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        /** Reduce one buffered draft to rows (one per multi-valued combination). */
        private List<Map<String, Object>> expandDraftRows(Map<String, Object> cols) {
            List<Map<String, Object>> out = new ArrayList<>();
            out.add(new LinkedHashMap<String, Object>());
            for (Map.Entry<String, Object> c : cols.entrySet()) {
                List<Object> values = c.getValue() instanceof List<?> list
                        ? new ArrayList<Object>(list)
                        : List.of(c.getValue());
                List<Map<String, Object>> next = new ArrayList<>();
                for (Map<String, Object> base : out) {
                    for (Object v : values) {
                        Map<String, Object> row = new LinkedHashMap<>(base);
                        row.put(c.getKey(), v);
                        next.add(row);
                    }
                }
                out = next;
            }
            return out;
        }

        private void flushSubject(String subject, Map<String, Map<String, Object>> byTable) {
            for (Map.Entry<String, Map<String, Object>> tableEntry : byTable.entrySet()) {
                RelationSchema schema = null;
                for (RelationSchema candidate : model.tables()) {
                    if (candidate.qualifiedName().equals(tableEntry.getKey())) {
                        schema = candidate;
                        break;
                    }
                }
                if (schema == null) {
                    continue;
                }
                Map<String, Object> draft = tableEntry.getValue();

                // Complete any key component the draft does not carry from the
                // individual's joined subject (a single-subject write into a
                // composite-key table carries only its data column).
                String[] subjectParts = subject.split("\u0000", -1);
                Map<String, Object> completeDraft = new LinkedHashMap<>(draft);
                List<String> pk = schema.primaryKey();
                for (int i = 0; i < pk.size(); i++) {
                    completeDraft.putIfAbsent(pk.get(i),
                            i < subjectParts.length ? subjectParts[i] : null);
                }

                for (Map<String, Object> rowCols : expandDraftRows(completeDraft)) {
                    flushRow(schema, subject, rowCols);
                }
            }
        }

        private void flushRow(RelationSchema schema, String subject,
                              Map<String, Object> rowCols) {
            List<String> pk = schema.primaryKey();
            // Split the draft into its key values, its buffered fact values,
            // and its retracted columns.
            List<String> keyVals = new ArrayList<>();
            boolean keyMissing = false;
            boolean keyRetract = false;
            Map<String, Object> facts = new LinkedHashMap<>();
            Set<String> retracted = new LinkedHashSet<>();
            boolean notNullRetract = false;
            for (String name : rowCols.keySet()) {
                Object v = rowCols.get(name);
                if (v == RETRACTED) {
                    retracted.add(name);
                    if (pk.contains(name)) {
                        keyRetract = true;
                    } else {
                        // A mandatory fact without a default realises the row's
                        // existence: deferring a retract of it deletes the row,
                        // exactly as the immediate retract would.
                        for (RelationSchema.Column c : schema.columns()) {
                            if (c.column().equals(name) && c.mandatory()
                                    && c.defaultValue() == null) {
                                notNullRetract = true;
                            }
                        }
                    }
                } else if (pk.contains(name)) {
                    if (v == null) {
                        keyMissing = true;
                    }
                    keyVals.add(String.valueOf(v));
                } else {
                    facts.put(name, v);
                }
            }
            try {
                if (keyRetract || keyMissing || notNullRetract) {
                    // A key-component retract, a missing key, or the deferred
                    // retract of a mandatory no-default fact removes the row
                    // (the individual or its defining fact ceases).
                    if (!keyVals.isEmpty() && keyVals.stream().noneMatch(v -> v.equals("null"))) {
                        deleteRowByCondition(
                                schema,
                                pk.size() == 1
                                        ? subjectField(schema).eq(subject)
                                        : compositeCondition(schema, keyVals));
                    }
                    return;
                }
                org.jooq.Condition keyCond = keyCondition(schema, keyVals, subject);
                if (dsl.fetchCount(table(schema), keyCond) > 0) {
                    // Existing individual/row: apply the buffered facts and any
                    // retracted columns' Rmap defaults; never touch the key.
                    Map<Field<?>, Object> set = new LinkedHashMap<>();
                    for (Map.Entry<String, Object> f : facts.entrySet()) {
                        set.put(DSL.field(DSL.name(f.getKey())), f.getValue());
                    }
                    for (String r : retracted) {
                        set.put(DSL.field(DSL.name(r)), defaultOrNothing(schema, r));
                    }
                    if (!set.isEmpty()) {
                        dsl.update(table(schema)).set(set).where(keyCond).execute();
                    }
                } else {
                    // New row: the buffered facts plus the Rmap defaults for
                    // retracted columns. If a mandatory (NOT NULL) column is
                    // absent, the database rejects the row — surfacing a
                    // model/action bug rather than inventing a value.
                    Map<Field<?>, Object> insert = new LinkedHashMap<>();
                    for (Map.Entry<String, Object> e : rowCols.entrySet()) {
                        Object v = e.getValue();
                        if (v == RETRACTED) {
                            v = defaultOrNothing(schema, e.getKey());
                        }
                        if (v != null) {
                            insert.put(DSL.field(DSL.name(e.getKey())), v);
                        } else if (pk.contains(e.getKey())) {
                            insert.put(DSL.field(DSL.name(e.getKey())), null);
                        }
                    }
                    dsl.insertInto(table(schema)).set(insert).execute();
                }
            } catch (org.jooq.exception.DataAccessException e) {
                throw new PostgresFactStore.UncheckedSQLException(new SQLException(e));
            }
        }

        /** A retracted column's stored value at flush: its Rmap default, or nothing. */
        private Object defaultOrNothing(RelationSchema schema, String colName) {
            for (RelationSchema.Column c : schema.columns()) {
                if (c.column().equals(colName) && c.defaultValue() != null) {
                    return fromSpi(c, c.defaultValue());
                }
            }
            return null;
        }

        private org.jooq.Condition keyCondition(RelationSchema schema, List<String> keyVals,
                                                String subject) {
            List<String> pk = schema.primaryKey();
            if (pk.size() == 1) {
                return subjectField(schema).eq(subject);
            }
            return compositeCondition(schema, keyVals);
        }

        private void deleteRow(RelationSchema schema, Map<String, Object> keyValues) {
            org.jooq.Condition cond = null;
            for (String name : keyValues.keySet()) {
                org.jooq.Condition c =
                        DSL.field(DSL.name(name), String.class).eq(String.valueOf(keyValues.get(name)));
                cond = cond == null ? c : cond.and(c);
            }
            dsl.deleteFrom(table(schema)).where(cond).execute();
        }

        private void deleteRowByCondition(RelationSchema schema, org.jooq.Condition cond) {
            dsl.deleteFrom(table(schema)).where(cond).execute();
        }

        private void clearRowBySubject(RelationSchema schema, String subject) {
            dsl.deleteFrom(table(schema)).where(subjectField(schema).eq(subject)).execute();
        }

        private List<org.jooq.Field<?>> conflictFields(RelationSchema schema) {
            List<Field<?>> out = new ArrayList<>();
            for (String pk : schema.primaryKey()) {
                out.add(DSL.field(DSL.name(pk)));
            }
            return out;
        }

        private void writeColumn(RelationSchema schema, RelationSchema.Column col,
                                 String subject, Object typed) {
            Map<Field<?>, Object> insert = new LinkedHashMap<>();
            insert.put(subjectField(schema), subject);
            insert.put(DSL.field(DSL.name(col.column())), typed);
            Map<Field<?>, Object> update = new LinkedHashMap<>();
            update.put(DSL.field(DSL.name(col.column())), typed);
            try {
                dsl.insertInto(table(schema)).set(insert)
                        .onConflict(conflictFields(schema)).doUpdate().set(update)
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
            RelationSchema schema = model.tableForPredicate(predicate);
            if (schema == null) {
                return;
            }
            // A composite-key table addressed by a joined subject (from facts()
            // / a caller round-tripping a fact's subject) is split back into its
            // component values.
            if (schema.primaryKey().size() > 1 && subject != null
                    && subject.split("\u0000", -1).length == schema.primaryKey().size()) {
                List<String> parts = new ArrayList<>(List.of(subject.split("\u0000", -1)));
                clear(parts, predicate);
                return;
            }
            RelationSchema.Column col = schema.columnFor(predicate);
            if (bufferRetract(schema, null, col, subject)) {
                return;
            }
            applyRetract(schema, col, subjectField(schema).eq(subject),
                    DSL.field(DSL.name(col.column())));
        }

        // ---- helpers --------------------------------------------------------

        private static boolean isKeyColumn(RelationSchema schema, RelationSchema.Column col) {
            return schema.primaryKey().contains(col.column());
        }

        private static Table<?> table(RelationSchema schema) {
            return DSL.table(DSL.name(schema.table()));
        }

        private static Field<String> subjectField(RelationSchema schema) {
            return DSL.field(DSL.name(schema.idColumn()), String.class);
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
            // The SPI's instant strings are ISO-8601 (the wire contract's
            // encoding); epoch-millis strings are accepted from legacy seeds.
            case "TIMESTAMP" -> value.chars().allMatch(Character::isDigit)
                    ? new Timestamp(Long.parseLong(value))
                    : Timestamp.from(java.time.Instant.parse(value));
            default -> value;
        };
    }

    /** Read a typed value back to the SPI's string form. */
    private static String toSpi(RelationSchema.Column col, Object value) {
        return switch (col.sqlType()) {
            case "INTEGER" -> String.valueOf(value);
            case "TIMESTAMP" -> ((Timestamp) value).toInstant().toString();
            default -> String.valueOf(value);
        };
    }
}
