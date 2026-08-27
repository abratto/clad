package com.example.app.architecture;

import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

/**
 * Machine-checks the WYSIWID hard rules for this (relational) profile.
 *
 * <p>R1 and R5 are profile-agnostic. R2 here is the relational analogue of the
 * RDF "one named graph per concept": a concept may only access JOOQ tables
 * whose owning prefix matches the concept's own name.
 */
class LegibleArchitectureRulesTest {

    private static final String CONCEPTS_ROOT = "com.example.app.concepts";
    private static final String DB_TABLES = "com.example.app.db.tables";

    private static final JavaClasses CLASSES = new ClassFileImporter()
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
            .importPackages("com.example.app", "dev.clad.engine");

    /** R1 — no cross-concept imports. */
    @Test
    void r1_no_cross_concept_imports() {
        noClasses()
                .that().resideInAPackage(CONCEPTS_ROOT + ".(*)..")
                .should().dependOnClassesThat(new DescribedPredicate<JavaClass>(
                        "reside in a sibling concept package") {
                    @Override
                    public boolean test(JavaClass dep) {
                        return dep.getPackageName().startsWith(CONCEPTS_ROOT + ".");
                    }
                })
                .andShould(new ArchCondition<JavaClass>("import a different concept's package") {
                    @Override
                    public void check(JavaClass item, ConditionEvents events) {
                        String myConcept = subPackageOf(item.getPackageName(), CONCEPTS_ROOT);
                        if (myConcept == null) return;
                        for (JavaClass dep : item.getDirectDependenciesFromSelf().stream()
                                .map(d -> d.getTargetClass()).toList()) {
                            String depConcept = subPackageOf(dep.getPackageName(), CONCEPTS_ROOT);
                            if (depConcept != null && !depConcept.equals(myConcept)) {
                                events.add(SimpleConditionEvent.violated(
                                        item, item.getName() + " imports " + dep.getName()
                                                + " across concept boundary (" + myConcept
                                                + " -> " + depConcept + ")"));
                            }
                        }
                    }
                })
                .check(CLASSES);
    }

    /** R2 (relational) — a JOOQ table is owned by exactly one concept. No two
     * concepts may reference the same generated table (one region per concept). */
    @Test
    void r2_no_cross_concept_table_access() throws IOException {
        Path conceptsRoot = Path.of("src/main/java/com/example/app/concepts");
        Pattern tableRef = Pattern.compile(Pattern.quote(DB_TABLES) + "\\.([A-Z][A-Za-z0-9]*)");
        Map<String, Set<String>> owners = new TreeMap<>();
        try (var dirs = Files.list(conceptsRoot)) {
            for (Path conceptDir : dirs.filter(Files::isDirectory).toList()) {
                String conceptName = conceptDir.getFileName().toString();
                try (var files = Files.walk(conceptDir)) {
                    for (Path javaFile : files.filter(p -> p.toString().endsWith(".java")).toList()) {
                        String text = Files.readString(javaFile);
                        Matcher matcher = tableRef.matcher(text);
                        while (matcher.find()) {
                            owners.computeIfAbsent(matcher.group(1),
                                    k -> new TreeSet<>()).add(conceptName);
                        }
                    }
                }
            }
        }
        for (var entry : owners.entrySet()) {
            if (entry.getValue().size() > 1) {
                throw new AssertionError(
                        "table '" + entry.getKey() + "' is referenced by multiple concepts "
                                + entry.getValue() + " — each concept owns its own table (R2).");
            }
        }
    }

    /** R5 — every {@code *Concept} class extends {@link dev.clad.engine.ConceptAgent}. */
    @Test
    void r5_every_concept_class_is_a_concept_agent() {
        classes()
                .that().resideInAPackage(CONCEPTS_ROOT + "..")
                .and().haveSimpleNameEndingWith("Concept")
                .should().beAssignableTo(dev.clad.engine.ConceptAgent.class)
                .check(CLASSES);
    }

    /** R3 — sync classes are declarative SyncAgent implementations. */
    @Test
    void r3_sync_package_classes_are_sync_agents() {
        classes()
                .that().resideInAPackage("com.example.app.syncs..")
                .and().areNotAnonymousClasses()
                .and().areNotMemberClasses()
                .and().haveNameNotMatching(".*\\$.*")
                .should().beAssignableTo(dev.clad.engine.SyncAgent.class)
                .check(CLASSES);
    }

    /** R4 — only infrastructure may carry Micronaut HTTP annotations. */
    @Test
    void r4_web_is_sole_http_entry() {
        noClasses()
                .that().resideOutsideOfPackage("com.example.app.infrastructure..")
                .should().beAnnotatedWith("io.micronaut.http.annotation.Controller")
                .orShould().beAnnotatedWith("io.micronaut.http.annotation.Get")
                .orShould().beAnnotatedWith("io.micronaut.http.annotation.Post")
                .check(CLASSES);
    }

    private static String subPackageOf(String pkg, String root) {
        if (!pkg.startsWith(root + ".")) return null;
        String tail = pkg.substring(root.length() + 1);
        int dot = tail.indexOf('.');
        return dot < 0 ? tail : tail.substring(0, dot);
    }
}
