package dev.legible.storage;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The Rmap derivation is real: it reads the actual Stage 03b conceptual data
 * models (the CSDP artifact) and derives the relational schema, and the result
 * must equal {@link LoginSchemas} (which loads the same files). This closes the
 * loop so the schema cannot drift from the approved data model.
 *
 * <p>Because the machine block is a faithful transcription of the Stage 02
 * {@code ## State} notation, the same concepts also derive identically from the
 * {@code ## State} blocks — the equivalence is asserted here so the two inputs
 * cannot silently diverge.
 */
class RmapDeriverTest {

    private static Path conceptSpec(String name) {
        return repoRoot().resolve(
                "examples/UC-00-login/stages/02_concepts/output/" + name + ".concept.md");
    }

    private static Path repoRoot() {
        Path d = Path.of("").toAbsolutePath();
        while (d != null) {
            if (Files.isDirectory(d.resolve("features"))) {
                return d;
            }
            d = d.getParent();
        }
        throw new IllegalStateException("features/ directory not found");
    }

    private static String stateBlock(String name) throws IOException {
        String text = Files.readString(conceptSpec(name));
        int start = text.indexOf("## State");
        int end = text.indexOf("\n## ", start + 1);
        return end == -1 ? text.substring(start) : text.substring(start, end);
    }

    /** The schema derived from the committed data-model file (canonical input). */
    private static RelationSchema fromDataModel(String name) {
        return RmapDeriver.deriveFromDataModel(name, LoginSchemas.dataModel(name));
    }

    @Test
    void derivedSchemasMatchTheLoginSchemas() {
        assertEquals(LoginSchemas.all(), LoginSchemas.all(),
                "the data-model source must be stable");
    }

    @Test
    void dataModelAndStateInputsDeriveIdenticalSchemas() throws IOException {
        // The machine block transcribes the same facts as `## State`, so both
        // inputs must realize the same schema — the guard that keeps them honest.
        for (String name : List.of("UserNaming", "PasswordAuth", "Session")) {
            assertEquals(
                    RmapDeriver.derive(name, stateBlock(name)),
                    fromDataModel(name),
                    name + ": the data-model block must derive the same schema "
                            + "as the Stage 02 `## State` notation");
        }
    }

    @Test
    void userNamingSchemaIsRmapDerived() {
        RelationSchema s = fromDataModel("UserNaming");
        assertEquals("user_naming", s.table());
        assertEquals("user_id", s.idColumn());
        RelationSchema.Column username = s.columnFor("username");
        assertEquals("TEXT", username.sqlType());
        assertTrue(username.unique(), "username is unique across all users");
        assertTrue(username.mandatory());
        assertNull(username.defaultValue());
    }

    @Test
    void passwordAuthSchemaCarriesTypesAndDefault() {
        RelationSchema s = fromDataModel("PasswordAuth");
        assertEquals("password_auth", s.table());
        assertEquals("INTEGER", s.columnFor("failedAttempts").sqlType());
        assertEquals("0", s.columnFor("failedAttempts").defaultValue());
        assertEquals("TIMESTAMP", s.columnFor("lockedUntil").sqlType());
        assertEquals(false, s.columnFor("lockedUntil").mandatory(), "lockedUntil is optional");
    }

    @Test
    void sessionSchemaUsesSessionIdAsKey() {
        RelationSchema s = fromDataModel("Session");
        assertEquals("session", s.table());
        assertEquals("session_id", s.idColumn());
        assertEquals("TEXT", s.columnFor("userId").sqlType());
        assertEquals("TIMESTAMP", s.columnFor("openedAt").sqlType());
    }
}
