package dev.legible.storage.domain;

import dev.legible.engine.Region;
import dev.legible.storage.RmapDeriver;
import dev.legible.storage.RmapModel;
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
                    "roles__client", "roles__supplier")) {
                st.execute("DROP TABLE IF EXISTS " + t + " CASCADE");
            }
        }
    }

    private RmapPostgresFactStore store(String domain, String concept) {
        RmapModel model = RmapDeriver.deriveModelFromDataModel(concept,
                DomainFixtures.dataModel(domain, concept));
        RmapPostgresFactStore store = new RmapPostgresFactStore(dataSource, model.tables());
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
        String state = """
                partyName: Party -> PartyName -- mandatory
                discountRate: Client -> Int -- optional
                creditLimit: Supplier -> Int -- optional
                Client is a Party -- mapping: partition
                Supplier is a Party -- mapping: partition
                """;
        RmapModel model = RmapDeriver.deriveModel("Roles", state);
        RmapPostgresFactStore store = new RmapPostgresFactStore(dataSource, model.tables());
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
        String plain = """
                copyCode: Copy -> CopyCode -- mandatory, unique
                title: Copy -> Title -- mandatory
                borrower: Loan -> Member -- mandatory
                openedAt: Loan -> Timestamp -- mandatory
                loanCopy: Loan -> Copy -- mandatory, unique
                returnedAt: Loan -> Timestamp -- optional
                """;
        RmapModel model = RmapDeriver.deriveModel("PlainLending", plain);
        RmapPostgresFactStore s2 = new RmapPostgresFactStore(dataSource, model.tables());
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
