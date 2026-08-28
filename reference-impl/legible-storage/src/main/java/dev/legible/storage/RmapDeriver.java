package dev.legible.storage;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Derives a {@link RelationSchema} from a concept's Stage 02 {@code ## State}
 * relational notation, by Halpin's Rmap rules.
 *
 * <p>The notation is {@code field: SubjectType -> FieldType -- annotations},
 * where annotations are {@code mandatory | optional}, {@code unique …}, and
 * {@code default <expr>}. The subject type becomes the primary key (snake_case);
 * each field becomes a typed column: {@code Int} → {@code INTEGER},
 * {@code Timestamp} → {@code TIMESTAMP}, and every other value type
 * ({@code String}, {@code PasswordHash}, {@code UserId}, …) → {@code TEXT}.
 * A {@code unique} annotation becomes {@code UNIQUE}; a {@code default} becomes
 * the reset-on-clear expression; {@code mandatory} is recorded as schema
 * metadata.
 */
public final class RmapDeriver {

    private static final Pattern STATE_LINE = Pattern.compile(
            "^\\s*(\\w+)\\s*:\\s*(\\w+)\\s*->\\s*(\\w+)\\s*(?:--\\s*(.*))?\\s*$");
    private static final Pattern DEFAULT = Pattern.compile("\\bdefault\\s+(\\w+)");

    private RmapDeriver() {
    }

    /**
     * Derive the schema for {@code concept} from its state notation.
     *
     * @param concept       the concept name (e.g. {@code "PasswordAuth"})
     * @param stateNotation the {@code ## State} block body, one relation per line
     */
    public static RelationSchema derive(String concept, String stateNotation) {
        String subjectType = null;
        List<RelationSchema.Column> columns = new ArrayList<>();

        for (String line : stateNotation.split("\\R")) {
            Matcher m = STATE_LINE.matcher(line);
            if (!m.matches()) {
                continue;
            }
            String field = m.group(1);
            String subject = m.group(2);
            String valueType = m.group(3);
            String annotations = m.group(4) == null ? "" : m.group(4);

            if (subjectType == null) {
                subjectType = subject;
            }
            boolean mandatory = annotations.contains("mandatory");
            boolean unique = annotations.contains("unique");
            String defaultValue = defaultOf(annotations);

            columns.add(new RelationSchema.Column(
                    field,
                    toSnakeCase(field),
                    sqlTypeOf(valueType),
                    mandatory,
                    unique,
                    defaultValue));
        }

        if (subjectType == null) {
            throw new IllegalArgumentException(
                    "no state relation parsed for concept " + concept);
        }
        return new RelationSchema(
                concept, toSnakeCase(concept), toSnakeCase(subjectType), columns);
    }

    private static String sqlTypeOf(String valueType) {
        return switch (valueType) {
            case "Int" -> "INTEGER";
            case "Timestamp" -> "TIMESTAMP";
            default -> "TEXT";
        };
    }

    private static String defaultOf(String annotations) {
        Matcher m = DEFAULT.matcher(annotations);
        return m.find() ? m.group(1) : null;
    }

    private static String toSnakeCase(String s) {
        return s.replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase();
    }
}
