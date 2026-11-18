package dev.legible.storage.domain;

import dev.legible.engine.Region;
import dev.legible.storage.RmapPostgresFactStore;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Edge-behavior probes over the fixture domains. Each probe pins the CURRENT
 * observable behavior of a documented risk; a changed assertion after a fix is
 * the intended upgrade path. Findings are recorded per test.
 */
class RmapEdgeBehaviorTest {

    private static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:16-alpine");

    private static PGSimpleDataSource dataSource;

    @BeforeAll
    static void startContainer() {
        POSTGRES.start();
        dataSource = new PGSimpleDataSource();
        dataSource.setUrl(POSTGRES.getJdbcUrl());
        dataSource.setUser(POSTGRES.getUsername());
        dataSource.setPassword(POSTGRES.getPassword());
    }

    @AfterAll
    static void stopContainer() {
        POSTGRES.stop();
    }

    @BeforeEach
    void reset() throws Exception {
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement()) {
            for (String t : List.of(
                    "patient_registry__person", "patient_registry__patient",
                    "order_intake", "order_intake__order_and_product", "order_intake__tags",
                    "lending__copy", "lending__loan", "hold__member_and_copy",
                    "roles__client", "roles__supplier",
                    "employment_conditional", "tenant_users",
                    "employment_discriminated", "rich_types")) {
                st.execute("DROP TABLE IF EXISTS " + t + " CASCADE");
            }
        }
    }

    private RmapPostgresFactStore store(String domain, String concept) {
        RmapPostgresFactStore store = new RmapPostgresFactStore(
                dataSource, DomainFixtures.schemas(domain, concept));
        store.createSchema();
        return store;
    }

    private boolean tableExists(String table) throws Exception {
        try (var c = dataSource.getConnection(); var rs = c.createStatement().executeQuery(
                "SELECT count(*) FROM information_schema.tables WHERE table_name = '" + table + "'")) {
            rs.next();
            return rs.getInt(1) > 0;
        }
    }

    private String cell(String table, String column, String where) throws Exception {
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement();
             ResultSet rs = st.executeQuery(
                     "SELECT " + column + " FROM " + table + " WHERE " + where)) {
            if (!rs.next()) {
                return null;
            }
            Object v = rs.getObject(1);
            return v == null ? null : String.valueOf(v);
        }
    }

    @Test
    @DisplayName("P1 separate-subtype: an orphan subtype write fails loudly on the FK; base+subtype writes join")
    void separateSubtypePopulationIsEnforcedByTheFk() throws Exception {
        // With intra-concept FKs rendered, `Patient is a Person` becomes the
        // population constraint the fact model always asserted: to be a
        // patient an individual must exist in the person table. No base-row
        // materializer — the concept action writes the supertype's facts.
        RmapPostgresFactStore store = store("clinic", "PatientRegistry");
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("PatientRegistry");

        var orphan = assertThrows(RuntimeException.class,
                () -> r.write("pat-9", "insurerName", "Orphan"),
                "a subtype individual with no supertype row is not a valid "
                        + "population state and must fail loudly");
        assertTrue(orphan.getMessage().contains("patient_registry__person"),
                "the FK names the missing base table: " + orphan.getMessage());
        assertEquals(0L, countRows("patient_registry__patient"));

        // The concept's action writes the base facts (buffered as one
        // statement), then the subtype fact joins on the shared identity.
        r.beginAction();
        r.write("pat-1", "registeredAt", "2026-10-04T09:00:00Z");
        r.write("pat-1", "gender", "F");
        r.flushAction();
        r.write("pat-1", "insurerName", "ACME");

        assertEquals(1L, countRows("patient_registry__person"));
        assertEquals(1L, countRows("patient_registry__patient"));
        assertEquals("ACME", cell("patient_registry__patient", "insurer_name",
                "person = 'pat-1'"));
        assertEquals("F", cell("patient_registry__person", "gender", "person = 'pat-1'"));
    }

    @Test
    @DisplayName("P2 CHECK constraint: out-of-enum writes are rejected")
    void checkConstraintRejectsOutOfEnumValues() {
        RmapPostgresFactStore store = store("ordering", "OrderIntake");
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("OrderIntake");

        // Buffer the individual's mandatory facts together (the production
        // pattern), carrying the out-of-enum status: the flush's INSERT must be
        // rejected by the CHECK, naming the constraint.
        r.beginAction();
        r.write("o-e2", "orderNumber", "E-2");
        r.write("o-e2", "totalCents", "0");
        r.write("o-e2", "status", "unknown");
        r.write("o-e2", "placedAt", "2026-10-04T12:00:00Z");
        var thrown = assertThrows(RuntimeException.class, r::flushAction,
                "an out-of-enum status must be rejected by the CHECK constraint");
        assertTrue(thrown.getMessage().contains("ck_order_status"),
                "the rejection should name the violated constraint: " + thrown.getMessage());

        // FINDING: an aborted action's buffer is empty, so every retry must
        // re-supply the individual's full mandatory fact set (the failed flush
        // left no row behind).
        r.beginAction();
        r.write("o-e2", "orderNumber", "E-2");
        r.write("o-e2", "totalCents", "0");
        r.write("o-e2", "status", "open");
        r.write("o-e2", "placedAt", "2026-10-04T12:00:00Z");
        r.flushAction();
        assertEquals(java.util.Set.of("open"), r.read("o-e2", "status"));
    }

    @Test
    @DisplayName("P3 partition: member-qualified operations route; plain operations on shared predicates throw at the operation")
    void partitionRoutingIsMemberAddressed() throws Exception {
        // UPGRADED (maintenance member-addressed-routing): the region is now
        // creatable — a partitioned supertype's shared (flattened) predicates
        // are addressed by member. A PLAIN operation on one throws at the
        // operation, naming the members; member-qualified operations route to
        // the member's own table, which is what makes a MANDATORY flattened
        // predicate satisfiable (the member's own row carries it).
        RmapPostgresFactStore store = new RmapPostgresFactStore(
                dataSource, DomainFixtures.customSchemas("Roles"));
        store.createSchema();
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("Roles");

        // The region is creatable, and a plain write on the shared predicate
        // throws naming the members and the member-qualified form.
        var plain = assertThrows(IllegalArgumentException.class,
                () -> r.write("cl-1", "partyName", "ClientCo"),
                "a plain operation on a flattened predicate is ambiguous");
        assertTrue(plain.getMessage().contains("partyName"), plain.getMessage());
        assertTrue(plain.getMessage().toLowerCase().contains("client")
                        && plain.getMessage().toLowerCase().contains("supplier"),
                "the error names the members: " + plain.getMessage());
        assertTrue(plain.getMessage().contains("member-qualified"),
                "the error names the member form: " + plain.getMessage());
        assertEquals(0L, countRows("roles__client"));

        // Member-qualified writes route to the member's table — one buffered
        // action can create the Client individual with its MANDATORY
        // flattened partyName satisfied by its own row.
        r.beginAction();
        r.write("Client", "cl-1", "partyName", "ClientCo");
        r.write("Client", "cl-1", "discountRate", "10");
        r.flushAction();
        assertEquals("ClientCo", cell("roles__client", "party_name", "party = 'cl-1'"),
                "the client's own row carries the mandatory flattened predicate");
        assertEquals("10", cell("roles__client", "discount_rate", "party = 'cl-1'"));
        assertEquals(0L, countRows("roles__supplier"), "no supplier row for a client");
        assertEquals(java.util.Set.of("ClientCo"), r.read("Client", "cl-1", "partyName"));

        // A second member lives wholly in its own table.
        r.beginAction();
        r.write("Supplier", "su-1", "partyName", "SupplierCo");
        r.write("Supplier", "su-1", "creditLimit", "5000");
        r.flushAction();
        assertEquals("SupplierCo", cell("roles__supplier", "party_name", "party = 'su-1'"));
        assertEquals("5000", cell("roles__supplier", "credit_limit", "party = 'su-1'"));
        assertEquals(1L, countRows("roles__client"), "the supplier never leaks into the client table");

        // Member retracts stay in the member's table.
        r.clear("Client", "cl-1", "discountRate");
        assertEquals(null, cell("roles__client", "discount_rate", "party = 'cl-1'"));
        assertEquals("ClientCo", cell("roles__client", "party_name", "party = 'cl-1'"));
    }

    @Test
    @DisplayName("P4 1:1 with history: filtered uniqueness allows a returned copy to be loaned again")
    void filteredUniquenessPreservesLoanHistory() throws Exception {
        // The fixture carves `loanCopy -- unique while returnedAt absent`, the
        // Postgres realisation being a partial unique index over loan_copy
        // filtered on returned_at IS NULL: at most one OPEN loan per copy.
        // The inline contrast keeps the plain-`unique` behavior visible.
        RmapPostgresFactStore store = store("lending", "Lending");
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("Lending");

        r.beginAction();
        r.write("c-1", "copyCode", "CB-1");
        r.write("c-1", "title", "Dune");
        r.flushAction();
        r.beginAction();
        r.write("l-1", "borrower", "m-1");
        r.write("l-1", "openedAt", "2026-10-01T10:00:00Z");
        r.write("l-1", "loanCopy", "c-1");
        r.flushAction();

        // While l-1 is open, a second loan of the same copy is rejected.
        r.beginAction();
        r.write("l-2", "borrower", "m-2");
        r.write("l-2", "openedAt", "2026-10-05T10:00:00Z");
        r.write("l-2", "loanCopy", "c-1");
        var openConflict = assertThrows(RuntimeException.class, r::flushAction,
                "at most one open loan per copy");
        assertTrue(openConflict.getMessage().toLowerCase().contains("open_idx")
                        || openConflict.getMessage().toLowerCase().contains("loan_copy"),
                "the rejection is the filtered unique index: "
                        + openConflict.getMessage());

        // Returning l-1 frees the copy: history preserved, l-2 may proceed.
        r.write("l-1", "returnedAt", "2026-10-04T10:00:00Z");
        r.beginAction();
        r.write("l-2", "borrower", "m-2");
        r.write("l-2", "openedAt", "2026-10-05T10:00:00Z");
        r.write("l-2", "loanCopy", "c-1");
        r.flushAction();
        assertEquals(java.util.Set.of("c-1"), r.read("l-2", "loanCopy"),
                "the copy is loaned again after its previous loan returned");
        assertEquals(2L, countRows("lending__loan"), "both loans persist");

        // Contrast — a plain `unique` (no filter) blocks history: even after
        // the return, the second loan cannot happen.
        RmapPostgresFactStore s2 = new RmapPostgresFactStore(
                dataSource, DomainFixtures.customSchemas("PlainLending"));
        s2.createSchema();
        dev.legible.engine.TransactionalRegion r2 =
                (dev.legible.engine.TransactionalRegion) s2.region("PlainLending");
        r2.beginAction();
        r2.write("c-1", "copyCode", "CB-1");
        r2.write("c-1", "title", "Dune");
        r2.flushAction();
        r2.beginAction();
        r2.write("l-1", "borrower", "m-1");
        r2.write("l-1", "openedAt", "2026-10-01T10:00:00Z");
        r2.write("l-1", "loanCopy", "c-1");
        r2.flushAction();
        r2.write("l-1", "returnedAt", "2026-10-04T10:00:00Z");
        r2.beginAction();
        r2.write("l-2", "borrower", "m-2");
        r2.write("l-2", "openedAt", "2026-10-05T10:00:00Z");
        r2.write("l-2", "loanCopy", "c-1");
        var plainConflict = assertThrows(RuntimeException.class, r2::flushAction,
                "plain unique forbids ever repeating the copy, filtered does not");
        assertTrue(plainConflict.getMessage().toLowerCase().contains("unique"),
                "the block is the plain UNIQUE constraint: "
                        + plainConflict.getMessage());
    }

    @Test
    @DisplayName("P6 absorbed subtype: mandatory facts are conditional, not NOT NULL")
    void absorbedSubtypeConditionalMandatoryIsEnforced() throws Exception {
        RmapPostgresFactStore store = new RmapPostgresFactStore(
                dataSource, DomainFixtures.customSchemas("EmploymentConditional"));
        store.createSchema();
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("EmploymentConditional");

        // Non-member: both guarded subtype columns are null.
        r.beginAction();
        r.write("p-1", "partyName", "Ada");
        r.flushAction();
        assertEquals(null,
                cell("employment_conditional", "vat_number", "party = 'p-1'"));
        assertEquals(null,
                cell("employment_conditional", "payroll_ref", "party = 'p-1'"));

        // Member: the mandatory qualifier and the optional fact are present.
        r.beginAction();
        r.write("p-2", "partyName", "ACME");
        r.write("p-2", "vatNumber", "VAT-1");
        r.write("p-2", "payrollRef", "PR-1");
        r.flushAction();
        assertEquals("VAT-1",
                cell("employment_conditional", "vat_number", "party = 'p-2'"));
        assertEquals("PR-1",
                cell("employment_conditional", "payroll_ref", "party = 'p-2'"));

        // Invalid: an optional subtype fact without the mandatory qualifier.
        r.beginAction();
        r.write("p-3", "partyName", "Solo");
        r.write("p-3", "payrollRef", "PR-3");
        var rejected = assertThrows(RuntimeException.class, r::flushAction,
                "a partial subtype population must fail the membership check");
        assertTrue(rejected.getMessage().toLowerCase().contains(
                        "ck_party_employer_member")
                        || rejected.getMessage().toLowerCase().contains("check"),
                "the rejection is the membership CHECK: "
                        + rejected.getMessage());
        assertEquals(null,
                cell("employment_conditional", "party", "party = 'p-3'"),
                "the rejected row never lands");
    }

    @Test
    @DisplayName("P8 concept action: promote a party to employer; partial promotion is rejected")
    void absorbedSubtypePromotionInActionBoundary() throws Exception {
        RmapPostgresFactStore store = new RmapPostgresFactStore(
                dataSource, DomainFixtures.customSchemas("EmploymentConditional"));
        store.createSchema();
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("EmploymentConditional");

        // Action 1 creates a non-employer; action 2 promotes the same row.
        r.beginAction();
        r.write("p1", "partyName", "Ada");
        r.flushAction();
        r.beginAction();
        r.write("p1", "vatNumber", "VAT-1");
        r.write("p1", "payrollRef", "PR-1");
        r.flushAction();
        assertEquals("VAT-1",
                cell("employment_conditional", "vat_number", "party = 'p1'"));
        assertEquals("PR-1",
                cell("employment_conditional", "payroll_ref", "party = 'p1'"));

        // A partial promotion in its own action leaves the row unchanged.
        r.beginAction();
        r.write("p2", "partyName", "Solo");
        r.flushAction();
        r.beginAction();
        r.write("p2", "payrollRef", "PR-2");
        assertThrows(RuntimeException.class, r::flushAction,
                "a partial promotion must fail the membership check");
        assertEquals(null,
                cell("employment_conditional", "vat_number", "party = 'p2'"));
        assertEquals(null,
                cell("employment_conditional", "payroll_ref", "party = 'p2'"));

        // Retracting only the qualifier would leave a partial member; the
        // action must retract both subtype facts together.
        r.beginAction();
        r.clear("p1", "vatNumber");
        assertThrows(RuntimeException.class, r::flushAction,
                "retracting only the qualifier leaves a partial member");
        r.beginAction();
        r.clear("p1", "vatNumber");
        r.clear("p1", "payrollRef");
        r.flushAction();
        assertEquals("Ada",
                cell("employment_conditional", "party_name", "party = 'p1'"),
                "the supertype row persists");
        assertEquals(null,
                cell("employment_conditional", "vat_number", "party = 'p1'"));
        assertEquals(null,
                cell("employment_conditional", "payroll_ref", "party = 'p1'"));
    }

    @Test
    @DisplayName("P7 entity reference: a same-concept FK rejects a missing target")
    void entityReferenceForeignKeyIsEnforced() throws Exception {
        RmapPostgresFactStore store = store("lending", "Lending");
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("Lending");

        r.beginAction();
        r.write("l-1", "borrower", "m-1");
        r.write("l-1", "openedAt", "2026-10-01T10:00:00Z");
        r.write("l-1", "loanCopy", "c-missing");
        var missing = assertThrows(RuntimeException.class, r::flushAction,
                "a loan must reference an existing copy");
        assertTrue(missing.getMessage().toLowerCase().contains("lending__copy")
                        || missing.getMessage().toLowerCase().contains(
                        "foreign key"),
                "the rejection is the copy FK: " + missing.getMessage());
        assertEquals(0L, countRows("lending__loan"));

        r.beginAction();
        r.write("c-1", "copyCode", "CB-1");
        r.write("c-1", "title", "Dune");
        r.flushAction();

        r.beginAction();
        r.write("l-1", "borrower", "m-1");
        r.write("l-1", "openedAt", "2026-10-01T10:00:00Z");
        r.write("l-1", "loanCopy", "c-1");
        r.flushAction();
        assertEquals(1L, countRows("lending__loan"));
    }

    @Test
    @DisplayName("P9 multi-column uniqueness is per tenant while the row is open")
    void multiColumnUniquenessWithinTenant() throws Exception {
        RmapPostgresFactStore store = new RmapPostgresFactStore(
                dataSource, DomainFixtures.customSchemas("TenantUsers"));
        store.createSchema();
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("TenantUsers");

        r.beginAction();
        r.write("u1", "tenant", "t1");
        r.write("u1", "email", "a@example.com");
        r.flushAction();
        r.beginAction();
        r.write("u2", "tenant", "t1");
        r.write("u2", "email", "b@example.com");
        r.flushAction();
        r.beginAction();
        r.write("u3", "tenant", "t2");
        r.write("u3", "email", "a@example.com");
        r.flushAction();

        // The same email in the same tenant is rejected.
        r.beginAction();
        r.write("u4", "tenant", "t1");
        r.write("u4", "email", "a@example.com");
        var duplicate = assertThrows(RuntimeException.class, r::flushAction,
                "tenant/email must be unique among open rows");
        assertTrue(duplicate.getMessage().toLowerCase().contains("open_idx")
                        || duplicate.getMessage().toLowerCase().contains(
                        "tenant_email"),
                "the rejection is the partial unique index: "
                        + duplicate.getMessage());

        // Soft-deleting the first row frees the pair.
        r.beginAction();
        r.write("u1", "deletedAt", "2026-01-01T00:00:00Z");
        r.flushAction();
        r.beginAction();
        r.write("u4", "tenant", "t1");
        r.write("u4", "email", "a@example.com");
        r.flushAction();
    }

    @Test
    @DisplayName("P10 explicit discriminator selects subtype membership")
    void discriminatorMembershipIsEnforced() throws Exception {
        RmapPostgresFactStore store = new RmapPostgresFactStore(
                dataSource,
                DomainFixtures.customSchemas("EmploymentDiscriminated"));
        store.createSchema();
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region(
                        "EmploymentDiscriminated");

        r.beginAction();
        r.write("p1", "partyName", "Ada");
        r.write("p1", "partyKind", "individual");
        r.flushAction();
        r.beginAction();
        r.write("p2", "partyName", "ACME");
        r.write("p2", "partyKind", "employer");
        r.write("p2", "vatNumber", "VAT-1");
        r.flushAction();

        r.beginAction();
        r.write("p3", "partyName", "Bad Individual");
        r.write("p3", "partyKind", "individual");
        r.write("p3", "vatNumber", "VAT-3");
        var individualWithVat = assertThrows(RuntimeException.class,
                r::flushAction,
                "an individual must not carry the employer fact");
        assertTrue(individualWithVat.getMessage().toLowerCase().contains(
                        "ck_party_employer_member"),
                individualWithVat.getMessage());

        r.beginAction();
        r.write("p4", "partyName", "Bad Employer");
        r.write("p4", "partyKind", "employer");
        var employerWithoutVat = assertThrows(RuntimeException.class,
                r::flushAction,
                "an employer must carry the mandatory VAT fact");
        assertTrue(employerWithoutVat.getMessage().toLowerCase().contains(
                        "ck_party_employer_member"),
                employerWithoutVat.getMessage());
    }

    @Test
    @DisplayName("P11 rich scalar types round-trip through the value codecs")
    void richScalarTypesRoundTrip() {
        RmapPostgresFactStore store = new RmapPostgresFactStore(
                dataSource, DomainFixtures.customSchemas("RichTypes"));
        store.createSchema();
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("RichTypes");

        r.beginAction();
        r.write("e1", "amount", "12.34");
        r.write("e1", "externalId", "550e8400-e29b-41d4-a716-446655440000");
        r.write("e1", "bornOn", "2026-01-31");
        r.write("e1", "opensAt", "09:30:00");
        r.write("e1", "metadata", "{\"a\": 1}");
        r.write("e1", "payload", "aGVsbG8=");
        r.flushAction();

        assertEquals(java.util.Set.of("12.34"), r.read("e1", "amount"));
        assertEquals(java.util.Set.of("550e8400-e29b-41d4-a716-446655440000"),
                r.read("e1", "externalId"));
        assertEquals(java.util.Set.of("2026-01-31"), r.read("e1", "bornOn"));
        assertEquals(java.util.Set.of("09:30:00"), r.read("e1", "opensAt"));
        String metadata = r.read("e1", "metadata").iterator().next();
        assertTrue(metadata.contains("\"a\""), metadata);
        assertEquals(java.util.Set.of("aGVsbG8="), r.read("e1", "payload"));
    }

    @Test
    @DisplayName("P5 optional objectified fact: retract NULLs the keyed row, identity persists")
    void optionalObjectifiedRetractNullsTheRow() throws Exception {
        // Contrast with a multi-valued child table (clear deletes the row): an
        // objectified (Member, Copy) hold is a keyed individual whose optional
        // value nulls out on retract while the identifying row remains.
        RmapPostgresFactStore store = store("lending", "Hold");
        Region r = store.region("Hold");

        r.write(List.of("m-1", "c-1"), "hold", "2");
        assertEquals(java.util.Set.of("2"), r.read(List.of("m-1", "c-1"), "hold"));

        r.clear(List.of("m-1", "c-1"), "hold");
        assertTrue(r.read(List.of("m-1", "c-1"), "hold").isEmpty(),
                "the priority fact is gone");
        assertEquals("1", cell("hold__member_and_copy", "count(*)", "member = 'm-1'"),
                "FINDING: the identifying row persists with a NULL priority");
    }

    private long countRows(String table) throws Exception {
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement();
             ResultSet rs = st.executeQuery("SELECT count(*) FROM " + table)) {
            rs.next();
            return rs.getLong(1);
        }
    }
}
