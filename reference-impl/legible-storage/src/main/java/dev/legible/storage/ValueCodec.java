package dev.legible.storage;

import org.jooq.DataType;

/**
 * Converts between the engine's string-oriented fact values and a column's
 * SQL type. Built-in codecs cover the CLAD core types; a downstream application
 * can register additional codecs through {@link ValueCodecs#register} or a
 * {@link java.util.ServiceLoader} provider.
 */
public interface ValueCodec {

    /** The base SQL type this codec handles (e.g. {@code NUMERIC}, {@code UUID}). */
    String sqlType();

    /** The jOOQ data type used to bind/read the column. */
    DataType<?> dataType();

    /** Convert the engine's string form into the JDBC/jOOQ value. */
    Object fromSpi(String value);

    /** Convert a JDBC/jOOQ value back to the engine's string form. */
    String toSpi(Object value);
}
