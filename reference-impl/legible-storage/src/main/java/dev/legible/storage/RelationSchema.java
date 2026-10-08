package dev.legible.storage;

import java.util.ArrayList;
import java.util.List;

/**
 * One relational table, derived from a concept's Stage 03b conceptual data
 * model by Halpin's <strong>Rmap</strong> (relation realization).
 *
 * <p>Each binary fact type over the concept's individual type becomes a typed
 * column absorbed into the owning object type's table; the individual
 * identifier is the primary key. Rmap's grouping rules decide <em>which</em>
 * table a fact type lands in:
 * <ul>
 *   <li><b>simple key</b> (a uniqueness constraint spanning one role) attached
 *       to an object type — the fact is a column on that object type's table;</li>
 *   <li><b>composite key</b> (a uniqueness constraint spanning more than one
 *       role) — the fact maps to its own table keyed on that composite;</li>
 *   <li><b>nested / objectified</b> fact type (a "compidot") — realised as a
 *       separate table, then unpacked into component attributes.</li>
 * </ul>
 * A concept's whole region is a {@link RmapModel} — a set of these tables.
 *
 * <p>Uniqueness from the fact model becomes a {@code UNIQUE} or {@code PRIMARY
 * KEY} constraint; mandatory roles become {@code NOT NULL}; value constraints
 * become {@code CHECK}; intra-concept references become foreign keys. Cross-
 * concept identifiers stay opaque typed columns — never a foreign key (R2).
 */
public record RelationSchema(
        String concept,
        String table,
        String objectType,
        List<Column> columns,
        List<String> primaryKey,
        List<String> foreignKeys,
        List<Check> checks,
        boolean derived) {

    /**
     * The historical single-scheme convenience constructor: {@code idColumn} is
     * both the object type name and the sole primary-key column.
     */
    public RelationSchema(String concept, String table, String idColumn,
                          List<Column> columns) {
        this(concept, table, idColumn, columns, List.of(idColumn),
                List.of(), List.of(), false);
    }

    public RelationSchema {
        columns = List.copyOf(columns);
        primaryKey = List.copyOf(primaryKey);
        foreignKeys = List.copyOf(foreignKeys);
        checks = List.copyOf(checks);
    }

    /** The concept-qualified table key (unique across a multi-table region). */
    public String qualifiedName() {
        return concept + "." + table;
    }

    /** The (first) object-identifier column. */
    public String idColumn() {
        return primaryKey.get(0);
    }

    /**
     * One fact-type column. {@code predicate} is the name the concept uses
     * through the {@code Region} SPI; {@code column} is the SQL column name;
     * {@code sqlType} is the Rmap-derived value type ({@code INTEGER},
     * {@code TIMESTAMP}, {@code TEXT}); {@code mandatory} records a mandatory
     * role (emitted as {@code NOT NULL}); {@code unique} marks a 1:1 /
     * alternate-key uniqueness constraint; {@code defaultValue} is the SQL
     * expression used when a fact is cleared and in the DDL's {@code DEFAULT}.
     * {@code valueConstraint} is an optional {@code CHECK} predicate (e.g. an
     * enum membership or a comparison). {@code uniqueWhileAbsent} is the optional
     * filtered-uniqueness field (from `unique while <field> absent`): the DDL
     * renderers emit a partial unique index on this column filtered on that
     * field's NULL — external uniqueness restricted to open individuals.
     */
    public record Column(
            String predicate,
            String column,
            String sqlType,
            boolean mandatory,
            boolean unique,
            String defaultValue,
            String valueConstraint,
            String uniqueWhileAbsent) {

        /** Convenience for the common no-value-constraint case. */
        public Column(String predicate, String column, String sqlType,
                      boolean mandatory, boolean unique, String defaultValue) {
            this(predicate, column, sqlType, mandatory, unique, defaultValue, null, null);
        }

        /** Convenience for the value-constraint case. */
        public Column(String predicate, String column, String sqlType,
                      boolean mandatory, boolean unique, String defaultValue,
                      String valueConstraint) {
            this(predicate, column, sqlType, mandatory, unique, defaultValue,
                    valueConstraint, null);
        }
    }

    /** A {@code CHECK} constraint over one or more columns. */
    public record Check(String name, String expression) {
    }

    /** The column realising the given fact-type predicate, or {@code null}. */
    public Column columnFor(String predicate) {
        return columns.stream()
                .filter(c -> c.predicate().equals(predicate))
                .findFirst()
                .orElse(null);
    }

    /**
     * The columns that carry the individual's key. Derived from the
     * {@code primaryKey}, not from the object-type name: the identity column is
     * named after the object type's reference scheme
     * ({@code object-type E identified-by I} -> column {@code snake(I)}), so
     * {@code snake(objectType)} no longer names it once the scheme is renamed.
     *
     * <p>A child table (composite PK over {@code (subject, value)}, single-
     * component object type) contributes only its subject column as identity;
     * its value column is data even though it sits inside the PK. A compound
     * (compidot) subject's object type carries {@code +}, so its whole PK is
     * identity.
     */
    public List<Column> identityColumns() {
        List<String> keyNames = !objectType.contains("+") && primaryKey.size() > 1
                ? primaryKey.subList(0, primaryKey.size() - 1)
                : primaryKey;
        java.util.Set<String> names = new java.util.LinkedHashSet<>(keyNames);
        return columns.stream()
                .filter(c -> names.contains(c.column()))
                .toList();
    }

    /** The columns carrying the individual's facts — everything but the key. */
    public List<Column> dataColumns() {
        List<Column> key = List.copyOf(identityColumns());
        return columns.stream()
                .filter(c -> !key.contains(c))
                .toList();
    }

    private static String snake(String s) {
        return s.replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase();
    }

    /**
     * The {@code CREATE TABLE} statement derived from this schema, plus
     * (rendered if present) the filtered-uniqueness partial indexes for its
     * columns. Intra-concept FKs are rendered as table constraints.
     */
    public String ddl() {
        boolean singlePk = primaryKey.size() == 1;
        String singleKeyCol = singlePk ? primaryKey.get(0) : null;
        StringBuilder sb = new StringBuilder();
        sb.append("CREATE TABLE IF NOT EXISTS \"").append(table).append("\" (\n");
        List<String> parts = new ArrayList<>();
        for (Column c : columns) {
            StringBuilder col = new StringBuilder();
            col.append(quote(c.column())).append(' ').append(c.sqlType());
            if (c.defaultValue() != null) {
                col.append(" DEFAULT ").append(c.defaultValue());
            }
            if (c.mandatory()) {
                col.append(" NOT NULL");
            }
            if (c.unique()) {
                col.append(" UNIQUE");
            }
            if (singlePk && c.column().equals(singleKeyCol)) {
                col.append(" PRIMARY KEY");
            }
            parts.add(col.toString());
        }
        if (!singlePk) {
            parts.add("PRIMARY KEY ("
                    + String.join(", ", primaryKey.stream().map(RelationSchema::quote).toList())
                    + ")");
        }
        for (Check check : checks) {
            parts.add("CONSTRAINT " + check.name() + " CHECK (" + check.expression() + ")");
        }
        for (String fk : foreignKeys) {
            parts.add(fkConstraint(fk));
        }
        sb.append("  ").append(String.join(",\n  ", parts));
        sb.append("\n)");
        // Filtered uniqueness emits its partial index after the table itself.
        for (Column c : columns) {
            if (c.uniqueWhileAbsent() != null) {
                sb.append(";\n").append(filteredIdx(table, c));
            }
        }
        return sb.toString();
    }

    private static String fkConstraint(String spec) {
        // Format: column -> table(target)
        int arrow = spec.indexOf("->");
        String column = spec.substring(0, arrow).trim();
        String ref = spec.substring(arrow + 2).trim();
        String target = ref.substring(ref.indexOf('(') + 1, ref.indexOf(')')).trim();
        String table = ref.substring(0, ref.indexOf('(')).trim();
        return "FOREIGN KEY (" + quote(column) + ") REFERENCES "
                + quote(table) + " (" + quote(target) + ")";
    }

    /** The partial unique index for a filtered-unique column. */
    private static String filteredIdx(String table, Column c) {
        return "CREATE UNIQUE INDEX IF NOT EXISTS "
                + quote(table + "_" + c.column() + "_open_idx")
                + " ON " + quote(table)
                + " (" + quote(c.column()) + ")"
                + " WHERE " + quote(snake(c.uniqueWhileAbsent())) + " IS NULL";
    }

    private static String quote(String ident) {
        return '"' + ident + '"';
    }
}
