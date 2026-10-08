package dev.legible.storage;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * {@link RmapDeriver#deriveModelFromDataModel} reads the CSDP-aligned
 * {@code ## Machine model} block from a Stage 03b data-model file: it ignores
 * the CSDP prose, drops {@code object-type} reference-scheme declarations, and
 * realizes the {@code fact} / {@code is a} / {@code independent} clauses. A file
 * without a machine block (or an unfenced one) must fail loudly rather than
 * derive an empty schema.
 */
class RmapDeriverDataModelTest {

    private static String dataModel(String machineBody) {
        return """
                # Example — conceptual data model

                ## Step 2 — Draft fact model and population check

                ### Fact types

                - `domain`

                ## Machine model

                ```
                """ + machineBody + """
                ```
                """;
    }

    @Test
    void derivesFromTheMachineBlockIgnoringProseAndObjectTypes() {
        String text = dataModel("""
                object-type ClientId identified-by ClientId
                fact domain : ClientId -> Domain -- mandatory
                fact createdAt : ClientId -> Timestamp -- mandatory
                """);
        RelationSchema s = RmapDeriver.deriveFromDataModel("Session", text);
        assertEquals("session", s.table());
        assertEquals("client_id", s.idColumn());
        assertNotNull(s.columnFor("domain"));
        assertNotNull(s.columnFor("createdAt"));
    }

    @Test
    void theIdentityColumnIsNamedAfterTheReferenceSchemeNotTheEntity() {
        // `object-type <Entity> identified-by <IdType>` names the identity
        // column after <IdType>, not after the entity.
        String text = dataModel("""
                object-type DrinkEntry identified-by EntryId
                fact entryId : DrinkEntry -> EntryId -- mandatory
                fact loggedAt : DrinkEntry -> Timestamp -- mandatory
                """);
        RelationSchema s = RmapDeriver.deriveFromDataModel("DrinkLogging", text);
        assertEquals("entry_id", s.idColumn(), "the column follows identified-by");
        assertNull(s.columnFor("drink_entry"),
                "the entity name is not used as a column");
    }

    @Test
    void aMultiValuedOnlySubjectEmitsNoIdentityOnlyTable() {
        // `AccountId` appears only as the subject of a multi-valued fact, so its
        // would-be table is identity-only and unpopulationable — it is not
        // emitted; the multi-valued fact still realises as its child table.
        String text = dataModel("""
                object-type AccountId identified-by AccountId
                object-type DrinkEntry identified-by DrinkEntry
                fact entries : AccountId -> { DrinkEntry } -- zero or more
                fact loggedAt : DrinkEntry -> Timestamp -- mandatory
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("DrinkLogging", text);
        assertTrue(model.tables().stream().noneMatch(t -> t.table().contains("account_id")),
                "no identity-only subject table");
        assertNotNull(model.tables().stream()
                .filter(t -> t.primaryKey().equals(java.util.List.of("account_id", "entries")))
                .findFirst().orElse(null),
                "the multi-valued fact still gets its child table");
    }

    @Test
    void compoundAndMultiValuedSubjectsRealiseAsATableSet() {
        String text = dataModel("""
                object-type FirmUri identified-by FirmUri
                object-type Service identified-by Service
                fact provides : FirmUri -> { Service } -- zero or more
                fact serviceJurisdiction : ( FirmUri, Service ) -> Jurisdiction -- optional
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("LegalOntology", text);
        // The multi-valued fact realizes as a composite-key child table, and the
        // compound (objectified) fact as its own compidot keyed on the parts.
        assertNotNull(model.tables().stream()
                .filter(t -> t.primaryKey().equals(java.util.List.of("firm_uri", "provides")))
                .findFirst().orElse(null),
                "the multi-valued fact gets its own child table");
        assertNotNull(model.tables().stream()
                .filter(t -> t.primaryKey().equals(java.util.List.of("firm_uri", "service")))
                .findFirst().orElse(null),
                "the (FirmUri, Service) fact gets its own compidot table");
    }

    @Test
    void aMissingMachineBlockThrows() {
        String text = "# Example — conceptual data model\n\n## Step 2\n\n- prose only\n";
        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> RmapDeriver.deriveModelFromDataModel("Example", text));
        assertEquals(true, ex.getMessage().contains("Machine model"));
    }

    @Test
    void anUnfencedMachineBlockThrows() {
        String text = "# Example\n\n## Machine model\n\nfact domain : ClientId -> Domain -- mandatory\n";
        assertThrows(IllegalArgumentException.class,
                () -> RmapDeriver.deriveModelFromDataModel("Example", text));
    }

    @Test
    void anEmptyBlockThrowsRatherThanDerivingNothing() {
        String text = dataModel("# no clauses\n");
        assertThrows(IllegalArgumentException.class,
                () -> RmapDeriver.deriveModelFromDataModel("Example", text));
    }

    @Test
    void subtypeMappingIsHonouredFromTheBlock() {
        String text = dataModel("""
                object-type Party identified-by Party
                Employer is a Party -- mapping: absorb
                fact partyName : Party -> PartyName -- mandatory
                fact vatNumber : Employer -> VatNumber -- mandatory
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("Employment", text);
        assertEquals(1, model.tables().size(), "absorption realizes one table");
        assertNotNull(model.tableFor("Party").columnFor("vatNumber"));
    }
}
