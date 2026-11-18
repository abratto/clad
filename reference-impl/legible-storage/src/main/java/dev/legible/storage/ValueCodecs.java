package dev.legible.storage;

import org.jooq.DataType;
import org.jooq.JSONB;
import org.jooq.impl.SQLDataType;

import java.math.BigDecimal;
import java.sql.Time;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.ServiceLoader;
import java.util.UUID;
import java.util.function.Function;

/**
 * Registry of {@link ValueCodec}s keyed by base SQL type.
 *
 * <p>The core CLAD types are built in. A downstream profile can register a
 * codec with {@link #register(ValueCodec)} or provide one through
 * {@code META-INF/services/dev.legible.storage.ValueCodec}. An unknown SQL type
 * fails loudly rather than silently binding as text.
 */
public final class ValueCodecs {

    private record SimpleCodec(
            String sqlType,
            DataType<?> dataType,
            Function<String, Object> decode,
            Function<Object, String> encode) implements ValueCodec {

        @Override
        public Object fromSpi(String value) {
            return decode.apply(value);
        }

        @Override
        public String toSpi(Object value) {
            return encode.apply(value);
        }
    }

    private static final DateTimeFormatter TIME_FORMAT =
            DateTimeFormatter.ofPattern("HH:mm:ss");
    private static final Map<String, ValueCodec> REGISTRY = new LinkedHashMap<>();

    static {
        register(new SimpleCodec(
                "TEXT", SQLDataType.VARCHAR, value -> value, String::valueOf));
        register(new SimpleCodec(
                "INTEGER", SQLDataType.INTEGER, Integer::parseInt, String::valueOf));
        register(new SimpleCodec(
                "TIMESTAMP", SQLDataType.TIMESTAMP,
                value -> value.chars().allMatch(Character::isDigit)
                        ? new Timestamp(Long.parseLong(value))
                        : Timestamp.from(Instant.parse(value)),
                value -> ((Timestamp) value).toInstant().toString()));
        register(new SimpleCodec(
                "BOOLEAN", SQLDataType.BOOLEAN, Boolean::parseBoolean,
                String::valueOf));
        register(new SimpleCodec(
                "NUMERIC", SQLDataType.NUMERIC, BigDecimal::new,
                value -> ((BigDecimal) value).toPlainString()));
        register(new SimpleCodec(
                "UUID", SQLDataType.UUID, UUID::fromString,
                value -> ((UUID) value).toString()));
        register(new SimpleCodec(
                "DATE", SQLDataType.DATE,
                value -> java.sql.Date.valueOf(LocalDate.parse(value)),
                value -> ((java.sql.Date) value).toLocalDate().toString()));
        register(new SimpleCodec(
                "TIME", SQLDataType.TIME,
                value -> Time.valueOf(LocalTime.parse(value)),
                value -> ((Time) value).toLocalTime().format(TIME_FORMAT)));
        register(new SimpleCodec(
                "JSONB", SQLDataType.JSONB, JSONB::valueOf,
                value -> ((JSONB) value).data()));
        register(new SimpleCodec(
                "BYTEA", SQLDataType.BINARY,
                value -> Base64.getDecoder().decode(value),
                value -> Base64.getEncoder().encodeToString((byte[]) value)));
        ServiceLoader.load(ValueCodec.class).forEach(ValueCodecs::register);
    }

    private ValueCodecs() {
    }

    /** Register or replace a codec for its base SQL type. */
    public static synchronized void register(ValueCodec codec) {
        REGISTRY.put(baseType(codec.sqlType()), codec);
    }

    /** The codec for a SQL type, ignoring an optional precision/scale suffix. */
    public static ValueCodec forType(String sqlType) {
        String base = baseType(sqlType);
        ValueCodec codec = REGISTRY.get(base);
        if (codec == null) {
            throw new IllegalArgumentException(
                    "no ValueCodec for SQL type '" + sqlType + "'; register a "
                            + "dev.legible.storage.ValueCodec provider or add "
                            + "a built-in mapping");
        }
        return codec;
    }

    private static String baseType(String sqlType) {
        String text = sqlType == null ? "" : sqlType.trim();
        int paren = text.indexOf('(');
        if (paren >= 0) {
            text = text.substring(0, paren).trim();
        }
        return text.toUpperCase(Locale.ROOT);
    }
}
