package dev.legible.storage;

import java.util.List;

/**
 * One concept's relational schema, derived from its Stage 03b conceptual data
 * model by Halpin's **Rmap**. Each binary fact type over the concept's
 * individual type becomes a typed column absorbed into the entity's table; the
 * individual identifier is the primary key. Uniqueness from the fact model
 * becomes a {@code UNIQUE} constraint.
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
     * {@code sqlType} is the Rmap-derived value type; {@code unique} marks a
     * 1:1 uniqueness constraint from the fact model.
     */
    public record Column(String predicate, String column, String sqlType, boolean unique) {
    }

    /** The {@code CREATE TABLE} statement derived from this schema. */
    public String ddl() {
        StringBuilder sb = new StringBuilder();
        sb.append("CREATE TABLE IF NOT EXISTS ").append(table).append(" (\n");
        sb.append("  ").append(idColumn).append(" TEXT PRIMARY KEY");
        for (Column c : columns) {
            sb.append(",\n  ").append(c.column()).append(' ').append(c.sqlType());
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
