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
 * The Rmap derivation is real: it reads the actual Stage 02 concept specs and
 * derives the relational schema, and the result must equal {@link LoginSchemas}
 * (whose state notation is embedded verbatim). This closes the loop so the
 * schema cannot drift from the use-case spec.
 */
class RmapDeriverTest {

    private static Path conceptSpec(String name) {
        return repoRoot().resolve(
                "features/UC-00-login/stages/02_concepts/output/" + name + ".concept.md");
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

    @Test
    void derivedSchemasMatchTheLoginSchemas() throws IOException {
        List<RelationSchema> derived = List.of(
                RmapDeriver.derive("UserNaming", stateBlock("UserNaming")),
                RmapDeriver.derive("PasswordAuth", stateBlock("PasswordAuth")),
                RmapDeriver.derive("Session", stateBlock("Session")));
        assertEquals(LoginSchemas.all(), derived,
                "the embedded state notation must derive the same schema as the actual spec files");
    }

    @Test
    void userNamingSchemaIsRmapDerived() throws IOException {
        RelationSchema s = RmapDeriver.derive("UserNaming", stateBlock("UserNaming"));
        assertEquals("user_naming", s.table());
        assertEquals("user_id", s.idColumn());
        RelationSchema.Column username = s.columnFor("username");
        assertEquals("TEXT", username.sqlType());
        assertTrue(username.unique(), "username is unique across all users");
        assertTrue(username.mandatory());
        assertNull(username.defaultValue());
    }

    @Test
    void passwordAuthSchemaCarriesTypesAndDefault() throws IOException {
        RelationSchema s = RmapDeriver.derive("PasswordAuth", stateBlock("PasswordAuth"));
        assertEquals("password_auth", s.table());
        assertEquals("INTEGER", s.columnFor("failedAttempts").sqlType());
        assertEquals("0", s.columnFor("failedAttempts").defaultValue());
        assertEquals("TIMESTAMP", s.columnFor("lockedUntil").sqlType());
        assertEquals(false, s.columnFor("lockedUntil").mandatory(), "lockedUntil is optional");
    }

    @Test
    void sessionSchemaUsesSessionIdAsKey() throws IOException {
        RelationSchema s = RmapDeriver.derive("Session", stateBlock("Session"));
        assertEquals("session", s.table());
        assertEquals("session_id", s.idColumn());
        assertEquals("TEXT", s.columnFor("userId").sqlType());
        assertEquals("TIMESTAMP", s.columnFor("openedAt").sqlType());
    }
}
