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
            return rs.next() ? String.valueOf(rs.getObject(1)) : null;
        }
    }

    @Test
    @DisplayName("P1 separate-subtype: a subtype write does NOT materialize the base row")
    void subtypeWriteDoesNotMaterializeTheBaseRow() throws Exception {
        // FINDING: the region SPI writes facts per predicate, nothing writes the
        // supertype row, and intra-concept FKs are NOT rendered into DDL — so a
        // subtype individual can exist in `patient_registry__patient` with no
        // `patient_registry__person` row. The fact model says a Patient is a
        // Person; the physical state silently disagrees.
        RmapPostgresFactStore store = store("clinic", "PatientRegistry");
        dev.legible.engine.TransactionalRegion r = (dev.legible.engine.TransactionalRegion) store.region("PatientRegistry");

        r.write("pat-9", "insurerName", "Orphan");

        assertEquals("Orphan", cell("patient_registry__patient", "insurer_name",
                "person = 'pat-9'"), "the subtype row was written");
        assertEquals(0L, countRows("patient_registry__person"),
                "no person base row materializes behind the subtype row");
        assertTrue(r.read("pat-9", "registeredAt").isEmpty(),
                "the base facts are absent — the individual only half exists");

        // Once the base row is written the two halves join up.
        r.beginAction();
        r.write("pat-9", "registeredAt", "2026-10-04T09:00:00Z");
        r.write("pat-9", "gender", "F");
        r.flushAction();
        assertEquals(1L, countRows("patient_registry__person"));
        assertEquals("Orphan", cell("patient_registry__patient", "insurer_name",
                "person = 'pat-9'"));
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
    @DisplayName("P3 partition: shared predicates route to the first owner; the second member splits or fails")
    void partitionRoutingPinned() throws Exception {
        // Both members carry their own predicates; table order (and therefore
        // the "first owner" of the shared `partyName`) is the Client table.
        String base = """
                partyName: Party -> PartyName -- %s
                discountRate: Client -> Int -- optional
                creditLimit: Supplier -> Int -- optional
                Client is a Party -- mapping: partition
                Supplier is a Party -- mapping: partition
                """;

        // --- mandatory variant ---
        String mandatory = base.formatted("mandatory");
        RmapModel m1 = RmapDeriver.deriveModel("Roles", mandatory);
        RmapPostgresFactStore s1 = new RmapPostgresFactStore(dataSource, m1.tables());
        s1.createSchema();
        assertTrue(tableExists("roles__client") && tableExists("roles__supplier"),
                "each partition member gets its own table");
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) s1.region("Roles");

        // `partyName` routes to the FIRST owner (roles__client). Flushing a
        // supplier member routes its supertype fact into the client table and
        // its member fact into roles__supplier — where the flattened NOT NULL
        // `party_name` can never be satisfied. The second member is unwritable.
        r.beginAction();
        r.write("su-1", "partyName", "SupplierCo");
        r.write("su-1", "creditLimit", "5000");
        var thrown = assertThrows(RuntimeException.class, r::flushAction,
                "a mandatory flattened supertype column is unsatisfiable on the "
                        + "non-first member under predicate routing");
        assertTrue(thrown.getMessage().contains("party_name"),
                "the gap is the flattened party_name column: " + thrown.getMessage());
        // FINDING: the per-table flush leaves the routed row behind.
        assertEquals("SupplierCo", cell("roles__client", "party_name", "party = 'su-1'"),
                "the supplier's partyName landed in the CLIENT table");
        assertEquals(0L, countRows("roles__supplier"), "no supplier row survives");

        // --- optional variant (fresh tables: the first variant's mandatory
        // DDL would otherwise persist through IF NOT EXISTS) ---
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement()) {
            st.execute("DROP TABLE IF EXISTS roles__client CASCADE");
            st.execute("DROP TABLE IF EXISTS roles__supplier CASCADE");
        }
        String optional2 = base.formatted("optional");
        RmapModel m2 = RmapDeriver.deriveModel("Roles", optional2);
        RmapPostgresFactStore s2 = new RmapPostgresFactStore(dataSource, m2.tables());
        s2.createSchema();
        dev.legible.engine.TransactionalRegion r2 =
                (dev.legible.engine.TransactionalRegion) s2.region("Roles");

        // A first-owner member writes wholly into its table...
        r2.beginAction();
        r2.write("cl-1", "partyName", "ClientCo");
        r2.write("cl-1", "discountRate", "10");
        r2.flushAction();
        assertEquals("ClientCo", cell("roles__client", "party_name", "party = 'cl-1'"));
        assertEquals("10", cell("roles__client", "discount_rate", "party = 'cl-1'"));
        assertEquals(0L, countRows("roles__supplier"));

        // ...while a second-owner member SPLITS across one row in each table.
        r2.beginAction();
        r2.write("su-1", "partyName", "SupplierCo");
        r2.write("su-1", "creditLimit", "5000");
        r2.flushAction();
        assertEquals("SupplierCo", cell("roles__client", "party_name", "party = 'su-1'"),
                "the supertype fact still routes to the first owner's table");
        assertEquals("5000", cell("roles__supplier", "credit_limit", "party = 'su-1'"));
        assertEquals(2L, countRows("roles__client"),
                "FINDING: the supplier individual ALSO occupies a client-table row");
        assertEquals(1L, countRows("roles__supplier"));
    }

    @Test
    @DisplayName("P4 1:1 column UNIQUE blocks loan history on a copy")
    void columnUniqueBlocksLoanHistoryOnACopy() {
        // FINDING (the deferred 1:1 edge): `loanCopy -- unique` realizes as a
        // column UNIQUE, which forbids ever loaning the same copy again. "At
        // most one OPEN loan per copy" needs external-uniqueness-with-filter —
        // outside the current machine-model grammar. Recorded as the deferral's
        // evidence; model such facts without `unique` until the grammar grows.
        RmapPostgresFactStore store = store("lending", "Lending");
        dev.legible.engine.TransactionalRegion r = (dev.legible.engine.TransactionalRegion) store.region("Lending");

        r.beginAction();
        r.write("c-1", "copyCode", "CB-1");
        r.write("c-1", "title", "Dune");
        r.flushAction();

        r.beginAction();
        r.write("l-1", "borrower", "m-1");
        r.write("l-1", "openedAt", "2026-10-01T10:00:00Z");
        r.write("l-1", "loanCopy", "c-1");
        r.flushAction();

        // Return the loan: the copy is free again by every business meaning.
        r.write("l-1", "returnedAt", "2026-10-04T10:00:00Z");

        var thrown = assertThrows(RuntimeException.class, () -> {
            r.beginAction();
            r.write("l-2", "borrower", "m-2");
            r.write("l-2", "openedAt", "2026-10-05T10:00:00Z");
            r.write("l-2", "loanCopy", "c-1");
            r.flushAction();
        }, "the second loan of a RETURNED copy must fail on the column UNIQUE — "
                + "history is not expressible with a plain COLUMN UNIQUE");
        assertTrue(thrown.getMessage().toLowerCase().contains("unique")
                        || thrown.getMessage().toLowerCase().contains("loan_copy"),
                "the rejection should be the loan_copy uniqueness: " + thrown.getMessage());
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
