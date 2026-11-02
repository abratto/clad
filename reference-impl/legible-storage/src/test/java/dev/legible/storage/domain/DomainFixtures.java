package dev.legible.storage.domain;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;

/**
 * Classpath loader for the generated runtime schema descriptors used by the
 * domain runtime probes. Derivation lives in {@code quality-gate/rmap.py};
 * these fixtures are its committed output.
 */
public final class DomainFixtures {

    private DomainFixtures() {
    }

    /** The generated runtime schema descriptor for a fixture concept. */
    public static List<dev.legible.storage.RelationSchema> schemas(
            String domain, String concept) {
        return load("/domains/" + domain + "/" + concept + ".schema.json");
    }

    /** The generated descriptor for a custom state used by a runtime probe. */
    public static List<dev.legible.storage.RelationSchema> customSchemas(
            String name) {
        return load("/domains/custom/" + name + ".schema.json");
    }

    private static List<dev.legible.storage.RelationSchema> load(String resource) {
        try (var in = DomainFixtures.class.getResourceAsStream(resource)) {
            if (in == null) {
                throw new IllegalStateException("schema fixture not found: " + resource);
            }
            return dev.legible.storage.RmapSchemaLoader.load(in);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
