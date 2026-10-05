package dev.legible.storage.domain;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;

/**
 * Classpath loader for the domain-exercise fixtures: per concept a
 * {@code .state.txt}, a {@code .data-model.md} (with its
 * {@code ## Machine model} block), and a frozen {@code .migration.sql} DDL
 * oracle.
 */
public final class DomainFixtures {

    private DomainFixtures() {
    }

    /** The {@code ## State} block for a concept (the equivalence-oracle input). */
    public static String state(String domain, String concept) {
        return read(domain, concept + ".state.txt");
    }

    /** The committed Stage 03b data-model text for a concept. */
    public static String dataModel(String domain, String concept) {
        return read(domain, concept + ".data-model.md");
    }

    /** The frozen {@code RmapMigration} oracle for a concept. */
    public static String expectedMigration(String domain, String concept) {
        return read(domain, concept + ".migration.sql");
    }

    private static String read(String domain, String file) {
        try (var in = DomainFixtures.class.getResourceAsStream(
                "/domains/" + domain + "/" + file)) {
            if (in == null) {
                throw new IllegalStateException(
                        "fixture not found: domains/" + domain + "/" + file);
            }
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
