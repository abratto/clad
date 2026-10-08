package dev.legible.storage;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Rmap derivation across the shapes the real algorithm must handle beyond the
 * single-table login case: several reference schemes in one concept, a compound
 * (objectified) subject, a multi-valued fact, value constraints, and the
 * mandatory/NOT-NULL rule.
 */
class RmapDeriverModelTest {

    @Test
    void multipleObjectTypesRealiseAsMultipleTables() {
        // Two reference schemes in one concept (the PartnerMatching shape).
        String state = """
                partnerId: CoverageId -> PartnerId        -- mandatory
                domain: CoverageId -> Domain              -- mandatory
                jurisdiction: CoverageId -> Jurisdiction  -- mandatory
                capacity: CoverageId -> Int               -- mandatory, default 0
                firmCapacity: PartnerId -> Int            -- mandatory, default 0
                """;
        RmapModel model = RmapDeriver.deriveModel("PartnerMatching", state);
        assertEquals(2, model.tables().size(), "one table per object type");
        RelationSchema coverage = model.tableFor("CoverageId");
        RelationSchema firm = model.tableFor("PartnerId");
        assertNotNull(coverage);
        assertNotNull(firm);
        assertEquals("coverage_id", coverage.idColumn());
        assertEquals("partner_id", firm.idColumn());
        assertNotNull(coverage.columnFor("capacity"));
        assertNotNull(firm.columnFor("firmCapacity"));
    }

    @Test
    void compoundSubjectRealisesAsItsOwnTableWithComponents() {
        // The LegalOntology shape: (FirmUri, Service) -> Jurisdiction.
        String state = """
                firmByClientId: ClientId -> FirmUri                       -- mandatory
                provides: FirmUri -> Service                              -- zero or more
                serviceName: Service -> ServiceName                       -- mandatory
                serviceJurisdiction: (FirmUri, Service) -> Jurisdiction   -- optional
                """;
        RmapModel model = RmapDeriver.deriveModel("LegalOntology", state);
        // One table per simple object type + the compound compidot + the
        // multi-valued 'provides' child table.
        RelationSchema compidot = model.tables().stream()
                .filter(t -> t.primaryKey().size() > 1
                        && t.primaryKey().equals(List.of("firm_uri", "service")))
                .findFirst().orElse(null);
        assertNotNull(compidot, "the (FirmUri, Service) fact gets its own table");
        assertTrue(compidot.columns().stream().anyMatch(c -> c.column().equals("firm_uri")));
        assertTrue(compidot.columns().stream().anyMatch(c -> c.column().equals("service")));
        assertTrue(compidot.columns().stream().anyMatch(c -> c.column().equals("service_jurisdiction")));
    }

    @Test
    void multiValuedFactRealisesAsAChildTable() {
        String state = """
                firmByClientId: ClientId -> FirmUri    -- mandatory
                provides: FirmUri -> {Service}          -- zero or more
                """;
        RmapModel model = RmapDeriver.deriveModel("LegalOntology", state);
        RelationSchema child = model.tables().stream()
                .filter(t -> t.primaryKey().size() > 1)
                .findFirst().orElse(null);
        assertNotNull(child, "a multi-valued fact maps to a composite-key child table");
        assertEquals(List.of("firm_uri", "provides"), child.primaryKey());
    }

    @Test
    void mandatoryRolesBecomeNotNullAndOptionalDoNot() {
        String state = """
                domain: ClientId -> Domain       -- mandatory
                createdAt: ClientId -> Timestamp -- mandatory
                triageSessionId: ClientId -> TriageSessionId -- optional
                """;
        RelationSchema t = RmapDeriver.derive("Session", state);
        assertTrue(t.columnFor("domain").mandatory());
        assertTrue(t.columnFor("createdAt").mandatory());
        assertEquals("TIMESTAMP", t.columnFor("createdAt").sqlType());
        assertFalse(t.columnFor("triageSessionId").mandatory());
    }

    @Test
    void valueConstraintRealisesAsACheck() {
        String state = """
                eventType: FactId -> EventType  -- mandatory, in {interaction, extraction, mismatch}
                recordedAt: FactId -> Timestamp -- mandatory
                """;
        RelationSchema t = RmapDeriver.derive("AnalyticsView", state);
        assertEquals(1, t.checks().size());
        assertTrue(t.checks().get(0).expression().contains("IN ('interaction', 'extraction', 'mismatch')"));
        assertTrue(t.ddl().contains("CHECK"));
    }

    @Test
    void uniqueRolesBecomeUniqueAndDefaultIsCarried() {
        String state = """
                username: UserId -> Username    -- mandatory, unique across all users
                """;
        RelationSchema t = RmapDeriver.derive("UserNaming", state);
        assertTrue(t.columnFor("username").unique());
    }

    @Test
    void defaultIsCarriedIntoDdl() {
        String state = """
                failedAttempts: UserId -> Int  -- mandatory, default 0
                """;
        RelationSchema t = RmapDeriver.derive("PasswordAuth", state);
        assertEquals("0", t.columnFor("failedAttempts").defaultValue());
        assertTrue(t.ddl().contains("DEFAULT 0"));
    }

    @Test
    void ddlEmitsNotNullForMandatoryColumns() {
        String state = """
                domain: ClientId -> Domain       -- mandatory
                triageSessionId: ClientId -> TriageSessionId -- optional
                """;
        String ddl = RmapDeriver.derive("WidgetSession", state).ddl();
        assertTrue(ddl.contains("\"domain\" TEXT NOT NULL"), ddl);
        assertTrue(!ddl.contains("\"triage_session_id\" TEXT NOT NULL"), ddl);
    }

    @Test
    void filteredUniquenessCarriesTheFieldAndEmitsAPartialIndex() {
        String state = """
                loanCopy: LoanId -> Copy     -- mandatory, unique while returnedAt absent
                returnedAt: LoanId -> Timestamp -- optional
                """;
        RelationSchema t = RmapDeriver.derive("LendingProbe", state);
        RelationSchema.Column lc = t.columnFor("loanCopy");
        // Filtered uniqueness replaces the unconditional column UNIQUE.
        assertTrue(!lc.unique(),
                "no standalone UNIQUE — uniqueness applies to open individuals only");
        assertEquals("returnedAt", lc.uniqueWhileAbsent(),
                "the filter field is carried on the column model");
        assertTrue(t.columnFor("copyCode2") == null
                        || !t.columnFor("copyCode2").unique(),
                "no phantom column");
        assertTrue(t.ddl().contains("CREATE UNIQUE INDEX IF NOT EXISTS "
                + "\"lending_probe_loan_copy_open_idx\""), t.ddl());
        assertTrue(t.ddl().contains("\"returned_at\" IS NULL"), t.ddl());
    }

    @Test
    void childTableForeignKeysNameTheSubjectTableAndColumn() {
        String state = """
                orderNumber: Order -> OrderNumber -- mandatory
                tags: Order -> { Tag }            -- zero or more
                """;
        List<RelationSchema> children = RmapDeriver.childTablesFor("Intake", state);
        assertEquals(1, children.size());
        assertEquals("order -> intake(order)",
                children.get(0).foreignKeys().get(0),
                "the FK targets the subject's own table and identity column");
    }

    @Test
    void aChildTableWithAnIdentityOnlyParentCarriesNoForeignKey() {
        // FirmUri plays no functional role of its own (it appears only as an
        // objectified-pair component and as the multi-valued subject) — its
        // table is identity-only, so the provides child gets no FK.
        String state = """
                firmByClientId: ClientId -> FirmUri    -- mandatory
                provides: FirmUri -> {Service}          -- zero or more
                """;
        List<RelationSchema> children = RmapDeriver.childTablesFor("Ontology", state);
        assertEquals(1, children.size());
        assertEquals(List.of(), children.get(0).foreignKeys(),
                "an FK onto an identity-only parent is unpopulationable");
    }

    @Test
    void roleMembershipAsAnObjectifiedFactRealisesTheDiscriminatorJunction() {
        // The role-catalog recipe (RELATIONAL_LOWERING §partition remediation):
        // membership asserted as an objectified fact instead of an implied
        // subtype — one junction table carries the role discriminator and the
        // role-scoped columns; no partition, so every predicate has one owner.
        String state = """
                partyName: Party -> PartyName -- mandatory
                roleName: Role -> RoleName -- mandatory, unique
                memberSince: ( Party, Role ) -> Timestamp -- mandatory
                creditLimit: ( Party, Role ) -> Int -- optional
                discountRate: ( Party, Role ) -> Int -- optional
                """;
        RmapModel model = RmapDeriver.deriveModel("RoleAssignments", state);
        assertEquals(3, model.tables().size());
        RelationSchema party = model.tableFor("Party");
        RelationSchema role = model.tableFor("Role");
        RelationSchema junction = model.tables().stream()
                .filter(t -> t.primaryKey().size() == 2).findFirst().orElse(null);
        assertNotNull(party);
        assertNotNull(role);
        assertNotNull(junction, "the membership fact is the junction");
        assertEquals(java.util.List.of("party", "role"), junction.primaryKey(),
                "the discriminator pair IS the key");
        assertNotNull(junction.columnFor("memberSince"), "membership marker is a column");
        assertNotNull(junction.columnFor("creditLimit"), "role-scoped fact on the junction");
        assertNotNull(junction.columnFor("discountRate"));
        // Every data predicate has exactly one owner — runtime-routable.
        for (RelationSchema t : model.tables()) {
            for (RelationSchema.Column c : t.dataColumns()) {
                long owners = model.tables().stream()
                        .filter(other -> other.columnFor(c.predicate()) != null
                                && !other.primaryKey().contains(c.column()))
                        .count();
                assertEquals(1L, owners,
                        "data predicate '" + c.predicate() + "' is multi-owned");
            }
        }
    }

    // ---- subtyping (P3, maintenance rmap-subtyping) ------------------------

    @Test
    void subtypeAbsorptionPutsSubtypeRolesOnTheSupertypeTable() {
        String state = """
                Employer is a Party -- mapping: absorb
                partyName: Party -> PartyName       -- mandatory
                vatNumber: Employer -> VatNumber     -- mandatory
                """;
        RmapModel model = RmapDeriver.deriveModel("Employment", state);
        assertEquals(1, model.tables().size(), "absorption realises one table");
        RelationSchema t = model.tableFor("Party");
        assertNotNull(t.columnFor("partyName"), "the supertype's fact is a column");
        assertNotNull(t.columnFor("vatNumber"),
                "an absorbed subtype role is a column on the supertype's table");
        assertEquals("employment", t.table(),
                "the single realised table carries the concept's name");
    }

    @Test
    void subtypeSeparationRealisesItsOwnTableLinkedToTheSupertype() {
        String state = """
                Manager is a Staff -- mapping: separate
                staffName: Staff -> StaffName      -- mandatory
                budget: Manager -> Money            -- mandatory
                """;
        RmapModel model = RmapDeriver.deriveModel("Organisation", state);
        assertEquals(2, model.tables().size(), "separation realises two tables");
        RelationSchema staff = model.tableFor("Staff");
        RelationSchema manager = model.tables().stream()
                .filter(t -> t.table().equals("organisation__manager"))
                .findFirst().orElse(null);
        assertNotNull(staff);
        assertNotNull(manager);
        // A subtype has no reference scheme of its own: the row's key is the
        // supertype's identity, and the table reports the scheme it inherits.
        assertEquals(List.of("staff"), manager.primaryKey(),
                "the subtype table keys on the supertype's identity");
        assertEquals("Staff", manager.objectType(),
                "the subtype table reports the identity-owning scheme");
        assertEquals(1, manager.foreignKeys().size(),
                "the subtype's key links to the supertype's table (intra-concept FK)");
        assertTrue(manager.foreignKeys().get(0).contains("organisation__staff"),
                "the FK names the supertype's realised table");
        assertNotNull(manager.columnFor("budget"), "the subtype's own fact is a column");
    }

    @Test
    void subtypeDefaultsToSeparationWhenNoMappingIsDeclared() {
        String state = """
                Manager is a Staff
                staffName: Staff -> StaffName      -- mandatory
                budget: Manager -> Money            -- mandatory
                """;
        RmapModel model = RmapDeriver.deriveModel("Organisation", state);
        RelationSchema manager = model.tables().stream()
                .filter(t -> t.table().equals("organisation__manager"))
                .findFirst().orElse(null);
        assertNotNull(manager, "an undeclared mapping separates (deterministic default)");
        assertEquals(1, manager.foreignKeys().size());
    }

    @Test
    void subtypePartitionFlattensSupertypeRolesIntoEachMemberTable() {
        String state = """
                Individual is a Client -- mapping: partition
                Company is a Client -- mapping: partition
                clientName: Client -> ClientName  -- mandatory
                vatNumber: Company -> VatNumber   -- mandatory
                """;
        RmapModel model = RmapDeriver.deriveModel("ClientRegistry", state);
        // Only the two partition members carry rows; the supertype has none.
        RelationSchema company = model.tables().stream()
                .filter(t -> t.table().equals("client_registry__company"))
                .findFirst().orElse(null);
        RelationSchema individual = model.tables().stream()
                .filter(t -> t.table().equals("client_registry__individual"))
                .findFirst().orElse(null);
        assertNotNull(company, "each partition member is its own table");
        assertNotNull(individual, "each partition member is its own table");
        assertTrue(model.tables().stream().noneMatch(t -> t.table().equals("client_registry")),
                "partition carries the supertype's roles in the members, not a parent table");
        assertNotNull(company.columnFor("clientName"),
                "the supertype's fact is flattened into the member's table");
        assertNotNull(company.columnFor("vatNumber"), "the member's own fact is present");
        // The member's identity is the supertype's (inherited scheme).
        assertEquals(List.of("client"), company.primaryKey());
        assertEquals("Client", company.objectType());
    }

    @Test
    void aDroppedPartitionMemberDoesNotCollapseTheSurvivingMemberName() {
        // `Individual`'s only inherited fact is multi-valued, so its table is
        // not emitted (identity-only). `Company` then survives alone — but the
        // "single -> concept name" collapse must not fire while partition
        // membership is in play, or `tableForMember` would return null.
        String state = """
                Individual is a Client -- mapping: partition
                Company is a Client -- mapping: partition
                entries: Client -> { Entry } -- zero or more
                companyName: Company -> CompanyName -- mandatory
                """;
        RmapModel model = RmapDeriver.deriveModel("Registry", state);
        RelationSchema company = model.tableForMember("Company");
        assertNotNull(company, "the surviving partition member stays resolvable");
        assertEquals("registry__company", company.table());
        assertTrue(model.tables().stream().noneMatch(t -> t.table().equals("registry")),
                "the surviving member did not collapse to the concept name");
    }

    @Test
    void independentObjectTypeRealisesAsItsOwnSingleColumnTable() {
        String state = """
                domain: ClientId -> Domain    -- mandatory
                createdAt: ClientId -> Timestamp -- mandatory
                independent AuditRef
                """;
        RmapModel model = RmapDeriver.deriveModel("Whitelist", state);
        assertEquals(2, model.tables().size(),
                "an independent type gains its own single-column table");
        RelationSchema audit = model.tables().stream()
                .filter(t -> t.table().equals("whitelist__audit_ref"))
                .findFirst().orElse(null);
        assertNotNull(audit, "an independent type beside other tables is concept-qualified");
        assertEquals(List.of("audit_ref"), audit.primaryKey());
        assertEquals(1, audit.columns().size(), "an independent type has no facts of its own");
        assertTrue(audit.ddl().contains("PRIMARY KEY"), audit.ddl());
    }

    @Test
    void existingSchemasReDeriveByteIdentical() {
        // The P7 drift guard depends on derivation stability: the committed
        // UC-00 shapes must derive to exactly the DDL already shipped in
        // reference-impl/java-micronaut's V1 migration (varchar is the
        // migration renderer's TEXT spelling, not the deriver's).
        String userNaming = """
                username: UserId -> String   -- mandatory, unique across all users
                """;
        String passwordAuth = """
                passwordHash: UserId -> PasswordHash     -- mandatory
                failedAttempts: UserId -> Int            -- mandatory, default 0
                lockedUntil: UserId -> Timestamp         -- optional
                """;
        String session = """
                userId: SessionId -> UserId       -- mandatory
                openedAt: SessionId -> Timestamp  -- mandatory
                """;
        assertTrue(RmapDeriver.derive("UserNaming", userNaming).ddl()
                .contains("\"username\" TEXT NOT NULL UNIQUE"),
                "the frozen upstream shape is unchanged by the subtyping work");
        assertTrue(RmapDeriver.derive("PasswordAuth", passwordAuth).ddl()
                .contains("\"failed_attempts\" INTEGER DEFAULT 0 NOT NULL"),
                "the frozen upstream shape is unchanged by the subtyping work");
        assertTrue(RmapDeriver.derive("Session", session).ddl()
                .contains("\"opened_at\" TIMESTAMP NOT NULL"),
                "the frozen upstream shape is unchanged by the subtyping work");
    }

    private static void assertFalse(boolean b) {
        org.junit.jupiter.api.Assertions.assertFalse(b);
    }

    private static void assertFalse(boolean b, String message) {
        org.junit.jupiter.api.Assertions.assertFalse(b, message);
    }
}
