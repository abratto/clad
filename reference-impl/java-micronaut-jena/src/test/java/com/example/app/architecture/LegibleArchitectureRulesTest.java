package com.example.app.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import org.junit.jupiter.api.Test;

/**
 * Machine-checks the WYSIWID hard rules from
 * {@code methodology/implementation/RULES.md} on this profile. If any
 * of these fail, the build fails.
 */
class LegibleArchitectureRulesTest {

    private static final String SOURCE_ROOT = "src/main/java/com/example/app";
    private static final String TRANSPORT_BRANCH_WAIVER = "CLAD-ALLOW-TRANSPORT-BRANCH";

    private static final JavaClasses CLASSES = new ClassFileImporter()
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
            .importPackages("com.example.app");

    private static final String CONCEPTS_ROOT = "com.example.app.concepts";

    /** R1 — no cross-concept imports. */
    @Test
    void r1_no_cross_concept_imports() {
        noClasses()
                .that().resideInAPackage(CONCEPTS_ROOT + ".(*)..")
                .should()
                .dependOnClassesThat(new com.tngtech.archunit.base.DescribedPredicate<JavaClass>(
                        "reside in a sibling concept package") {
                    @Override
                    public boolean test(JavaClass dep) {
                        String pkg = dep.getPackageName();
                        if (!pkg.startsWith(CONCEPTS_ROOT + ".")) return false;
                        // Same concept package is fine.
                        return true;
                    }
                })
                .andShould(new ArchCondition<>("import a different concept's package") {
                    @Override
                    public void check(JavaClass item, ConditionEvents events) {
                        String myConcept = subPackageOf(item.getPackageName(), CONCEPTS_ROOT);
                        if (myConcept == null) return;
                        for (JavaClass dep : item.getDirectDependenciesFromSelf().stream()
                                .map(d -> d.getTargetClass()).toList()) {
                            String depConcept = subPackageOf(dep.getPackageName(), CONCEPTS_ROOT);
                            if (depConcept != null && !depConcept.equals(myConcept)) {
                                events.add(SimpleConditionEvent.violated(
                                        item,
                                        item.getName() + " imports " + dep.getName()
                                                + " across concept boundary ("
                                                + myConcept + " -> " + depConcept + ")"));
                            }
                        }
                    }
                })
                .check(CLASSES);
    }

    /** R4 — only WebConcept may carry Micronaut HTTP annotations. */
    @Test
    void r4_web_is_sole_http_entry() {
        noClasses()
                .that().resideOutsideOfPackage("com.example.app.infrastructure..")
                .should().beAnnotatedWith("io.micronaut.http.annotation.Controller")
                .orShould().beAnnotatedWith("io.micronaut.http.annotation.Get")
                .orShould().beAnnotatedWith("io.micronaut.http.annotation.Post")
                .orShould().beAnnotatedWith("io.micronaut.http.annotation.Put")
                .orShould().beAnnotatedWith("io.micronaut.http.annotation.Delete")
                .check(CLASSES);
    }

    /** R4 — the HTTP boundary must not depend on business concepts directly. */
    @Test
    void r4_web_boundary_does_not_depend_on_business_concepts() {
        noClasses()
                .that().resideInAPackage("com.example.app.infrastructure..")
                .and().haveSimpleNameContaining("Web")
                .should().dependOnClassesThat().resideInAPackage(CONCEPTS_ROOT + "..")
                .as("Web/infrastructure entry classes must stay transport-only and not depend on business concepts directly")
                .check(CLASSES);
    }

    /**
     * R4 (heuristic) — Web boundary code must not perform imperative branching
     * on business outcomes in controller source. If a transport-only branch is
     * genuinely required, it must carry the explicit waiver marker.
     */
    @Test
    void r4_web_boundary_has_no_imperative_branching_without_transport_waiver() throws IOException {
        List<Path> webSources = Files.walk(Path.of(SOURCE_ROOT, "infrastructure"))
                .filter(path -> path.getFileName().toString().contains("Web"))
                .filter(path -> path.toString().endsWith(".java"))
                .toList();

        for (Path path : webSources) {
            List<String> lines = Files.readAllLines(path);
            for (int index = 0; index < lines.size(); index++) {
                String line = lines.get(index);
                String trimmed = line.trim();
                if (trimmed.startsWith("//") || trimmed.startsWith("*") || trimmed.startsWith("/*")) {
                    continue;
                }
                if ((trimmed.contains("if (") || trimmed.contains("switch (") || trimmed.startsWith("case "))
                        && !trimmed.contains(TRANSPORT_BRANCH_WAIVER)) {
                    throw new AssertionError(
                            path + ":" + (index + 1)
                                    + " contains imperative branching in Web boundary code."
                                    + " Move domain branching to syncs/concepts or annotate a transport-only exception with "
                                    + TRANSPORT_BRANCH_WAIVER + ".");
                }
            }
        }
    }

    /**
     * R5 — every {@code *Concept} class under {@code com.example.app.concepts}
     * must extend {@link com.example.app.engine.ConceptAgent}, ensuring it
     * participates in the action-log polling loop. Every action it executes
     * therefore has an addressable flow token in the RDF store.
     */
    @Test
    void r5_every_concept_class_is_a_concept_agent() {
        classes()
                .that().resideInAPackage(CONCEPTS_ROOT + "..")
                .and().haveSimpleNameEndingWith("Concept")
                .should().beAssignableTo(com.example.app.engine.ConceptAgent.class)
                .check(CLASSES);
    }

    /**
     * R2 (heuristic) — each concept package contains exactly one
     * {@code *Concept} class, which is taken as that concept's owning
     * region. Stronger graph-level R2 enforcement will follow when the
     * RDF backend lands.
     */
    @Test
    void r2_one_concept_class_per_concept_package() {
        classes()
                .that().resideInAPackage(CONCEPTS_ROOT + ".(*)")
                .and().haveSimpleNameEndingWith("Concept")
                .should(new ArchCondition<>("be the only *Concept class in their package") {
                    @Override
                    public void check(JavaClass item, ConditionEvents events) {
                        long siblings = CLASSES.stream()
                                .filter(c -> c.getPackageName().equals(item.getPackageName()))
                                .filter(c -> c.getSimpleName().endsWith("Concept"))
                                .count();
                        if (siblings != 1) {
                            events.add(SimpleConditionEvent.violated(
                                    item,
                                    "package " + item.getPackageName()
                                            + " contains " + siblings + " *Concept classes (R2 expects 1)"));
                        }
                    }
                })
                .check(CLASSES);
    }

    /**
     * R3 (heuristic) — sync classes must not hold mutable state. We
     * approximate by forbidding non-final instance fields on classes
     * under {@code com.example.app.syncs}. The seed has no syncs yet,
     * so this test passes vacuously today; the rule is active for any
     * sync added later.
     */
    @Test
    void r3_syncs_have_no_mutable_state() {
        classes()
                .that().resideInAPackage("com.example.app.syncs..")
                .should().haveOnlyFinalFields()
                .as("syncs must have only final fields (R3)")
                .allowEmptyShould(true)
                .check(CLASSES);
    }

    private static String subPackageOf(String pkg, String root) {
        if (!pkg.startsWith(root + ".")) return null;
        String tail = pkg.substring(root.length() + 1);
        int dot = tail.indexOf('.');
        return dot < 0 ? tail : tail.substring(0, dot);
    }
}
