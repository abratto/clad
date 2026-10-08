package dev.legible.storage;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
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
    void aRenamedSchemeIsUsedByChildTableColumnsAndForeignKey() {
        // The reference-scheme rename must reach the child table too: its
        // subject column and the FK target are the parent's identity column
        // (`entry_id`), never the entity name (`drink_entry`).
        String text = dataModel("""
                object-type DrinkEntry identified-by EntryId
                fact loggedAt : DrinkEntry -> Timestamp -- mandatory
                fact tags : DrinkEntry -> { Tag } -- zero or more
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("DrinkLogging", text);
        RelationSchema parent = model.tableFor("DrinkEntry");
        assertNotNull(parent);
        assertEquals("entry_id", parent.idColumn());
        RelationSchema child = model.tables().stream()
                .filter(t -> t.primaryKey().size() == 2).findFirst().orElseThrow();
        assertTrue(child.primaryKey().contains("entry_id"),
                "the child's subject column follows the reference scheme");
        assertEquals("entry_id -> " + parent.table() + "(entry_id)",
                child.foreignKeys().get(0),
                "the FK references the parent's identity column, not the entity");
        assertFalse(child.ddl().contains("drink_entry"),
                "no dangling column in the child DDL: " + child.ddl());
    }

    @Test
    void identityColumnsFollowTheRenamedScheme() {
        // The identity-column set must be derived from the primary key, not the
        // object-type name — otherwise a renamed scheme yields no identity
        // column and `facts()` corrupts the full-state read.
        String text = dataModel("""
                object-type DrinkEntry identified-by EntryId
                fact loggedAt : DrinkEntry -> Timestamp -- mandatory
                """);
        RelationSchema s = RmapDeriver.deriveFromDataModel("DrinkLogging", text);
        assertEquals(java.util.List.of("entry_id"),
                s.identityColumns().stream().map(RelationSchema.Column::column).toList(),
                "identity follows the renamed PK");
        assertTrue(s.dataColumns().stream().noneMatch(c -> c.column().equals("entry_id")),
                "the key is not a data column");
    }

    @Test
    void anIndependentTypeColumnFollowsTheReferenceScheme() {
        String text = dataModel("""
                object-type Widget identified-by WidgetId
                object-type ClientId identified-by ClientId
                fact domain : ClientId -> Domain -- mandatory
                independent Widget
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("Whitelist", text);
        RelationSchema widget = model.tables().stream()
                .filter(t -> t.table().equals("whitelist__widget"))
                .findFirst().orElseThrow();
        assertEquals(java.util.List.of("widget_id"), widget.primaryKey());
    }

    @Test
    void aMultiValuedFactOnASubtypeSubjectLinksByIdentityColumn() {
        String text = dataModel("""
                object-type Person identified-by PersonId
                Patient is a Person -- mapping: separate
                fact personName : Person -> PersonName -- mandatory
                fact diagnosis : Patient -> Diagnosis -- mandatory
                fact allergies : Patient -> { Allergy } -- zero or more
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("Registry", text);
        RelationSchema child = model.tables().stream()
                .filter(t -> t.primaryKey().size() == 2).findFirst().orElseThrow();
        assertEquals(java.util.List.of("person_id", "allergies"), child.primaryKey());
        assertEquals("person_id -> registry__patient(person_id)",
                child.foreignKeys().get(0),
                "the child keys on the subtype's inherited identity column");
    }

    @Test
    void aMultiValuedFactOnAnAbsorbedSubjectLinksToTheSupertypeTable() {
        String text = dataModel("""
                object-type Party identified-by PartyId
                Employer is a Party -- mapping: absorb
                fact partyName : Party -> PartyName -- mandatory
                fact vatNumber : Employer -> VatNumber -- mandatory
                fact tags : Employer -> { Tag } -- zero or more
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("Employment", text);
        RelationSchema child = model.tables().stream()
                .filter(t -> t.primaryKey().size() == 2).findFirst().orElseThrow();
        assertEquals(java.util.List.of("party_id", "tags"), child.primaryKey());
        assertEquals("party_id -> employment(party_id)", child.foreignKeys().get(0),
                "an absorbed subject's rows live in the supertype's table");
    }

    @Test
    void compoundComponentColumnsFollowTheReferenceScheme() {
        String text = dataModel("""
                object-type Party identified-by PartyId
                object-type Service identified-by ServiceId
                fact partyName : Party -> PartyName -- mandatory
                fact serviceName : Service -> ServiceName -- mandatory
                fact serviceJurisdiction : ( Party, Service ) -> Jurisdiction -- optional
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("LegalOntology", text);
        RelationSchema compidot = model.tables().stream()
                .filter(t -> t.primaryKey().size() == 2).findFirst().orElseThrow();
        assertEquals(java.util.List.of("party_id", "service_id"), compidot.primaryKey(),
                "compidot components follow each type's reference scheme");
    }

    @Test
    void aSubtypeUnderARenamedSchemeLinksByIdentityColumn() {
        // The subtype's inherited key and its FK both follow the supertype's
        // reference scheme (`person_id`), not the supertype entity (`person`).
        String text = dataModel("""
                object-type Person identified-by PersonId
                Patient is a Person -- mapping: separate
                fact personName : Person -> PersonName -- mandatory
                fact diagnosis : Patient -> Diagnosis -- mandatory
                """);
        RmapModel model = RmapDeriver.deriveModelFromDataModel("Registry", text);
        RelationSchema patient = model.tables().stream()
                .filter(t -> t.table().equals("registry__patient"))
                .findFirst().orElseThrow();
        assertEquals(java.util.List.of("person_id"), patient.primaryKey());
        assertEquals("person_id -> registry__person(person_id)",
                patient.foreignKeys().get(0),
                "the subtype FK uses the supertype's identity column");
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
