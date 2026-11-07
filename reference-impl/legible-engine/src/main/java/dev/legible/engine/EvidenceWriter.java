package dev.legible.engine;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * Writes a completed flow's runtime evidence to a JSON file for the Acceptance
 * Spec comparison ({@code quality-gate/acceptance_evidence.py}).
 *
 * <p>Each file is {@code <dir>/<scenario>.json} with the shape a live
 * {@code GET /api/dev/flow/{id}} returns ({@code flowId}, {@code actions}), plus
 * the bound {@code test} and an optional {@code readback} snapshot. The quality
 * gate assembles these into {@code acceptance-evidence.json} and compares them
 * to the frozen Acceptance Spec, so "the test predicts this path" is separated
 * from "the running app produced this path".
 *
 * <p>Dependency-free (no Jackson): the flow payload is maps, lists, strings,
 * numbers, and booleans, which are serialized directly.
 */
public final class EvidenceWriter {

    private final Path dir;

    private EvidenceWriter(Path dir) {
        this.dir = dir;
    }

    /** A writer rooted at {@code dir} (created on first write). */
    public static EvidenceWriter to(String dir) {
        return new EvidenceWriter(Path.of(dir));
    }

    /** Write the latest archived flow as {@code <scenario>.json} (no read-back). */
    public void write(String scenario, SyncEngine engine, String test) {
        write(scenario, engine, test, null);
    }

    /**
     * Write the latest archived flow as {@code <scenario>.json}.
     *
     * @param scenario the Acceptance-Spec scenario name
     * @param engine   the engine that just ran the flow
     * @param test     the bound test method ({@code Class.method})
     * @param readback an optional persisted read-back snapshot (persistent profile)
     */
    public void write(String scenario, SyncEngine engine, String test,
                      Map<String, Object> readback) {
        FlowRecord record = engine.archiver().buffer().latest()
                .orElseThrow(() -> new IllegalStateException(
                        "no archived flow to capture for scenario " + scenario));
        Map<String, Object> payload = new java.util.LinkedHashMap<>(
                engine.debug().flow(record.flowId()));
        payload.put("test", test);
        if (readback != null) {
            payload.put("readback", readback);
        }
        try {
            Files.createDirectories(dir);
            Files.writeString(dir.resolve(scenario + ".json"), json(payload),
                    StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException(
                    "could not write evidence for " + scenario, e);
        }
    }

    // --- minimal JSON serialization (maps/lists/scalars) -------------------

    private static String json(Object value) {
        StringBuilder sb = new StringBuilder();
        write(sb, value);
        return sb.toString();
    }

    private static void write(StringBuilder sb, Object value) {
        if (value == null) {
            sb.append("null");
        } else if (value instanceof String s) {
            quote(sb, s);
        } else if (value instanceof Number || value instanceof Boolean) {
            sb.append(value);
        } else if (value instanceof Map<?, ?> map) {
            sb.append('{');
            boolean first = true;
            for (Map.Entry<?, ?> e : map.entrySet()) {
                if (!first) {
                    sb.append(',');
                }
                first = false;
                quote(sb, String.valueOf(e.getKey()));
                sb.append(':');
                write(sb, e.getValue());
            }
            sb.append('}');
        } else if (value instanceof Iterable<?> items) {
            sb.append('[');
            boolean first = true;
            for (Object item : items) {
                if (!first) {
                    sb.append(',');
                }
                first = false;
                write(sb, item);
            }
            sb.append(']');
        } else if (value instanceof Object[] array) {
            write(sb, List.of(array));
        } else {
            quote(sb, value.toString());
        }
    }

    private static void quote(StringBuilder sb, String text) {
        sb.append('"');
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            switch (c) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (c < 0x20) {
                        sb.append(String.format("\\u%04x", (int) c));
                    } else {
                        sb.append(c);
                    }
                }
            }
        }
        sb.append('"');
    }
}
