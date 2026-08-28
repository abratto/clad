package dev.legible.storage;

import java.util.List;

/**
 * One concept's relational schema, derived from its Stage 03b conceptual data
 * model by Halpin's **Rmap**. Each binary fact type over the concept's
 * individual type becomes a typed column absorbed into the entity's table; the
 * individual identifier is the primary key. Uniqueness from the fact model
 * becomes a {@code UNIQUE} constraint; mandatory roles become {@code NOT NULL}.
 *
 * <p>This is "relation realization" — the deterministic, normalized, keyed,
 * constrained schema — as opposed to "fact realization" (a generic
 * {@code fact(concept, subject, predicate, value)} relation, see
 * {@link PostgresFactStore}).
 */
public record RelationSchema(
        String concept,
        String table,
        String idColumn,
        List<Column> columns) {

    /**
     * One fact-type column. {@code predicate} is the name the concept uses
     * through the {@code Region} SPI; {@code column} is the SQL column name;
     * {@code sqlType} is the Rmap-derived value type ({@code TEXT},
     * {@code INTEGER}, {@code TIMESTAMP}); {@code mandatory} records a
     * mandatory role from the fact model (schema metadata — see below);
     * {@code unique} marks a 1:1 uniqueness constraint; {@code defaultValue} is
     * the SQL expression used when a fact is cleared (reset-to-default) and in
     * the DDL's {@code DEFAULT} clause.
     *
     * <p>The engine's {@code Region} SPI writes facts one at a time
     * ({@code write(subject, predicate, value)}), so a concept with several
     * mandatory facts cannot satisfy a row-level {@code NOT NULL} atomically —
     * the first write would leave the other mandatory columns null. {@code
     * mandatory} is therefore recorded here for Stage 04a traceability, but is
     * not emitted as {@code NOT NULL}; typed columns, {@code DEFAULT}, and
     * {@code UNIQUE} are enforced by the database.
     */
    public record Column(
            String predicate,
            String column,
            String sqlType,
            boolean mandatory,
            boolean unique,
            String defaultValue) {
    }

    /** The {@code CREATE TABLE} statement derived from this schema. */
    public String ddl() {
        StringBuilder sb = new StringBuilder();
        sb.append("CREATE TABLE IF NOT EXISTS ").append(table).append(" (\n");
        sb.append("  ").append(idColumn).append(" TEXT PRIMARY KEY");
        for (Column c : columns) {
            sb.append(",\n  ").append(c.column()).append(' ').append(c.sqlType());
            if (c.defaultValue() != null) {
                sb.append(" DEFAULT ").append(c.defaultValue());
            }
            if (c.unique()) {
                sb.append(" UNIQUE");
            }
        }
        sb.append("\n)");
        return sb.toString();
    }

    /** The column realising the given fact-type predicate, or {@code null}. */
    public Column columnFor(String predicate) {
        return columns.stream()
                .filter(c -> c.predicate().equals(predicate))
                .findFirst()
                .orElse(null);
    }
}
