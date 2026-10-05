package dev.legible.storage.domain;

import dev.legible.storage.RmapDeriver;
import dev.legible.storage.RmapMigration;
import dev.legible.storage.RmapModel;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.fail;

/**
 * Domain exercise, derivation half: for every fixture concept the data model's
 * {@code ## Machine model} block must derive exactly the same tables as the
 * same facts in {@code ## State} form, and the rendered Flyway migration must
 * be byte-identical to the frozen oracle.
 */
class RmapDomainDerivationTest {

    /** Every fixture concept, as (domain, concept, single-table-expected). */
    static List<String[]> allConcepts() {
        return List.of(
                new String[]{"clinic", "Scheduling"},
                new String[]{"clinic", "PatientRegistry"},
                new String[]{"ordering", "OrderIntake"},
                new String[]{"lending", "Lending"},
                new String[]{"lending", "Hold"});
    }

    @ParameterizedTest(name = "{0}: machine block matches ## State")
    @CsvSource({
            "clinic, Scheduling",
            "clinic, PatientRegistry",
            "ordering, OrderIntake",
            "lending, Lending",
            "lending, Hold",
    })
    void machineBlockMatchesTheStateNotation(String domain, String concept) {
        var fromBlock = RmapDeriver.deriveModelFromDataModel(concept,
                DomainFixtures.dataModel(domain, concept));
        var fromState = RmapDeriver.deriveModel(concept,
                DomainFixtures.state(domain, concept));
        assertEquals(fromState, fromBlock,
                domain + "/" + concept + ": the data-model block must derive the "
                        + "same schema as the Stage 02 state notation");
    }

    @Test
    void everyFixtureConceptIsCoveredByAnOracle() {
        for (String[] c : allConcepts()) {
            try {
                var expected = DomainFixtures.expectedMigration(c[0], c[1]);
                if (expected.isBlank()) {
                    fail(c[0] + "/" + c[1] + ": empty migration oracle");
                }
            } catch (IllegalStateException e) {
                fail("missing migration oracle for " + c[0] + "/" + c[1]
                        + " (" + e.getMessage() + ")");
            }
        }
    }

    @ParameterizedTest(name = "{0}: frozen migration oracle")
    @CsvSource({
            "clinic, Scheduling",
            "clinic, PatientRegistry",
            "ordering, OrderIntake",
            "lending, Lending",
            "lending, Hold",
    })
    void migrationRendersByteIdenticalToTheOracle(String domain, String concept) {
        RmapModel model = RmapDeriver.deriveModelFromDataModel(concept,
                DomainFixtures.dataModel(domain, concept));
        String rendered = RmapMigration.renderModels(concept + " (domain fixture)",
                List.of(model));
        assertEquals(DomainFixtures.expectedMigration(domain, concept), rendered,
                domain + "/" + concept + ": the rendered migration drifted from "
                        + "the frozen oracle — re-freeze only after reviewing the "
                        + "derivation change");
    }
}
