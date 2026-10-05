package dev.legible.storage;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * The UC-00-login relational schemas, <em>derived</em> from the Stage 03b
 * conceptual data models' {@code ## Machine model} blocks by
 * {@link RmapDeriver} — not hand-authored.
 *
 * <p>The canonical Rmap input is the Stage 03b data model (the CSDP artifact),
 * not the Stage 02 {@code ## State} notation: the data model is where the
 * elementary facts and constraints are approved. This loader reads the
 * committed {@code <Name>.data-model.md} files and derives from their machine
 * blocks; {@link RmapDeriverTest} re-reads the same files and asserts the
 * derivation matches, so the schema cannot drift from the data model.
 */
public final class LoginSchemas {

    private LoginSchemas() {
    }

    /** The concept names, in schema order. */
    private static final List<String> CONCEPTS = List.of("UserNaming", "PasswordAuth", "Session");

    public static List<RelationSchema> all() {
        return CONCEPTS.stream()
                .map(name -> RmapDeriver.deriveFromDataModel(name, dataModel(name)))
                .toList();
    }

    /** The committed Stage 03b data-model text for {@code concept}. */
    public static String dataModel(String concept) {
        return read(dataModelPath(concept));
    }

    private static Path dataModelPath(String concept) {
        return repoRoot().resolve(
                "examples/UC-00-login/stages/03b_data-model/output/"
                        + concept + ".data-model.md");
    }

    private static Path repoRoot() {
        Path dir = Path.of("").toAbsolutePath();
        while (dir != null) {
            if (Files.isDirectory(dir.resolve("features"))) {
                return dir;
            }
            dir = dir.getParent();
        }
        throw new IllegalStateException(
                "repository root (features/) not found from "
                        + Path.of("").toAbsolutePath()
                        + " — the reference profile derives its schema from the "
                        + "committed Stage 03b data models; an app derived from this "
                        + "seed rebinds this loader to its own "
                        + "<Name>.data-model.md files.");
    }

    private static String read(Path path) {
        try {
            return Files.readString(path);
        } catch (IOException e) {
            throw new UncheckedIOException("cannot read data model " + path, e);
        }
    }
}
