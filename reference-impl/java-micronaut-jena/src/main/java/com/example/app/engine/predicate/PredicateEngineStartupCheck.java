package com.example.app.engine.predicate;

import com.example.app.engine.ConceptAgent;
import io.micronaut.context.annotation.Context;
import io.micronaut.context.annotation.Requires;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

/**
 * Validates that all concepts use the predicate engine when
 * {@code engine.mode=predicate} is set in {@code clad.properties}.
 *
 * <p>If a concept still extends {@link ConceptAgent} instead of
 * {@link PredicateConceptAgent}, startup fails with a clear message
 * telling the developer which concepts need migration.
 *
 * <p>This makes the {@code engine.mode} property functional — it's
 * not just documentation; it enforces the mode at startup.
 */
@Context
@Requires(property = "engine.mode", value = "predicate")
public class PredicateEngineStartupCheck {

    private static final Logger LOG = LoggerFactory.getLogger(PredicateEngineStartupCheck.class);

    private final List<ConceptAgent> allConcepts;

    public PredicateEngineStartupCheck(List<ConceptAgent> allConcepts) {
        this.allConcepts = allConcepts;
    }

    @PostConstruct
    void validate() {
        List<String> nonPredicate = allConcepts.stream()
                .filter(c -> !(c instanceof PredicateConceptAgent))
                .map(c -> c.getClass().getSimpleName())
                .toList();

        if (!nonPredicate.isEmpty()) {
            throw new IllegalStateException(
                    "engine.mode=predicate requires all concepts to extend "
                    + "PredicateConceptAgent. The following concepts still "
                    + "extend ConceptAgent: " + String.join(", ", nonPredicate)
                    + ". Change them to extend PredicateConceptAgent and add "
                    + "PredicateSyncDispatcher to the constructor. "
                    + "See reference-impl/java-micronaut-jena/README.md "
                    + "§'Using the predicate engine'.");
        }

        LOG.info("Predicate engine active — {} concept(s) validated", allConcepts.size());
    }
}
