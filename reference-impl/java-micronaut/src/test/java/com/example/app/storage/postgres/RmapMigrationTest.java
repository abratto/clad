package com.example.app.storage.postgres;

import dev.legible.storage.LoginSchemas;
import dev.legible.storage.RmapMigration;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Flyway owns DDL: the committed base migration must equal the R-map derivation
 * rendered by {@link RmapMigration}. This is the drift guard — change a concept
 * `## State` and this fails until the migration is regenerated.
 *
 * <p>Regenerate with {@code mvn test -Drmap.migration.write=true} (see
 * {@code RELATIONAL_LOWERING.md}).
 */
class RmapMigrationTest {

    private static final Path MIGRATION =
            Path.of("src/main/resources/db/migration/V1__login_rmap.sql");

    @Test
    void committedMigrationMatchesTheRmapDerivation() throws Exception {
        String expected = RmapMigration.render("UC-00-login (java-micronaut reference)",
                LoginSchemas.all());
        if (System.getProperty("rmap.migration.write") != null) {
            Files.writeString(MIGRATION, expected);
            System.out.println("WROTE " + MIGRATION);
            return;
        }
        assertEquals(expected, Files.readString(MIGRATION),
                "V1__login_rmap.sql is stale — regenerate it from LoginSchemas "
                        + "(mvn test -Drmap.migration.write=true; see RELATIONAL_LOWERING.md)");
    }
}
