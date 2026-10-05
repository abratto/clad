package dev.legible.storage.domain;

import dev.legible.engine.Region;
import dev.legible.storage.RmapDeriver;
import dev.legible.storage.RmapModel;
import dev.legible.storage.RmapPostgresFactStore;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Domain exercise, storage half: the fixture concepts round-trip through
 * {@link RmapPostgresFactStore} on a real Postgres — composite subjects,
 * multi-valued child tables, defaults, and subtype tables keyed on the
 * supertype's identity.
 */
class RmapDomainStorageTest {

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
                    "scheduling__physician_and_patient_and_timeslot",
                    "scheduling__physician_and_patient", "scheduling__referral_source",
                    "patient_registry__person", "patient_registry__patient",
                    "order_intake", "order_intake__order_and_product", "order_intake__tags",
                    "lending__copy", "lending__loan", "hold__member_and_copy")) {
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

    @Test
    void schedulingCompositeSubjectsRoundTrip() {
        RmapPostgresFactStore store = store("clinic", "Scheduling");
        Region r = store.region("Scheduling");

        r.write(List.of("ph-1", "pa-1", "ts-1"), "appt", "booked");
        assertEquals(Set.of("booked"), r.read(List.of("ph-1", "pa-1", "ts-1"), "appt"));

        // Same composite individual, new status: an update of the keyed row.
        r.write(List.of("ph-1", "pa-1", "ts-1"), "appt", "seen");
        assertEquals(Set.of("seen"), r.read(List.of("ph-1", "pa-1", "ts-1"), "appt"));

        // The pair-level fact lands in its own compidot table.
        r.write(List.of("ph-1", "pa-1"), "consultFee", "120");
        assertEquals(Set.of("120"), r.read(List.of("ph-1", "pa-1"), "consultFee"));
        r.write(List.of("ph-1", "pa-1"), "consultFee", "150");
        assertEquals(Set.of("150"), r.read(List.of("ph-1", "pa-1"), "consultFee"));

        // A second triple is its own row, never overwriting the first.
        r.write(List.of("ph-1", "pa-2", "ts-1"), "appt", "booked");
        assertEquals(Set.of("seen"), r.read(List.of("ph-1", "pa-1", "ts-1"), "appt"));
        assertEquals(Set.of("booked"), r.read(List.of("ph-1", "pa-2", "ts-1"), "appt"));
    }

    @Test
    void orderingMultiValuedChildTablesAndDefaults() {
        RmapPostgresFactStore store = store("ordering", "OrderIntake");
        dev.legible.engine.TransactionalRegion r = (dev.legible.engine.TransactionalRegion) store.region("OrderIntake");

        // The order's mandatory facts flush as one statement (buffered action).
        r.beginAction();
        r.write("o-1", "orderNumber", "100");
        r.write("o-1", "totalCents", "1999");
        r.write("o-1", "status", "open");
        r.write("o-1", "placedAt", "2026-10-04T12:00:00Z");
        r.flushAction();
        assertEquals(Set.of("open"), r.read("o-1", "status"));
        assertEquals(Set.of("1999"), r.read("o-1", "totalCents"));

        // Multi-valued tags append child rows; each value is its own row.
        r.write("o-1", "tags", "gift");
        r.write("o-1", "tags", "priority");
        assertEquals(Set.of("gift", "priority"), r.read("o-1", "tags"));

        // Line items objectified per (order, product).
        r.write(List.of("o-1", "p-1"), "line", "2");
        r.write(List.of("o-1", "p-2"), "line", "1");
        assertEquals(Set.of("2"), r.read(List.of("o-1", "p-1"), "line"));
        r.write(List.of("o-1", "p-1"), "line", "3");
        assertEquals(Set.of("3"), r.read(List.of("o-1", "p-1"), "line"));
        assertEquals(Set.of("1"), r.read(List.of("o-1", "p-2"), "line"));

        // Retracting the multi-valued fact deletes every child row for the order.
        r.clear("o-1", "tags");
        assertEquals(Set.of(), r.read("o-1", "tags"));

        // Retracting the counter resets to the Rmap default, not to nothing.
        r.clear("o-1", "totalCents");
        assertEquals(Set.of("0"), r.read("o-1", "totalCents"));
    }

    @Test
    void patientRegistrySubtypeTableKeysOnTheSupertypeIdentity() {
        RmapPostgresFactStore store = store("clinic", "PatientRegistry");
        dev.legible.engine.TransactionalRegion r = (dev.legible.engine.TransactionalRegion) store.region("PatientRegistry");

        // Base (supertype) facts first, then a subtype-specific fact for the
        // same individual: the patient row carries the person's key.
        r.beginAction();
        r.write("pat-1", "registeredAt", "2026-01-01T09:00:00Z");
        r.write("pat-1", "gender", "F");
        r.flushAction();
        r.write("pat-1", "insurerName", "ACME");

        assertEquals(Set.of("F"), r.read("pat-1", "gender"));
        assertEquals(Set.of("ACME"), r.read("pat-1", "insurerName"));
        Set<String> timestamps = r.read("pat-1", "registeredAt");
        assertEquals(1, timestamps.size());
        assertEquals("2026-01-01T09:00:00Z", Instant.parse(timestamps.iterator().next()).toString());
    }

    @Test
    void lendingOpenAndReturnALoan() {
        RmapPostgresFactStore store = store("lending", "Lending");
        dev.legible.engine.TransactionalRegion copy =
                (dev.legible.engine.TransactionalRegion) store.region("Lending");

        // Two mandatory facts on one individual flush as one statement (an
        // unbuffered single-fact write would violate NOT NULL before the
        // sibling arrives — the production path always goes through the engine
        // wrapper, which buffers the action).
        copy.beginAction();
        copy.write("c-1", "copyCode", "CB-1");
        copy.write("c-1", "title", "Dune");
        copy.flushAction();

        dev.legible.engine.TransactionalRegion loan = (dev.legible.engine.TransactionalRegion) store.region("Lending");
        loan.beginAction();
        loan.write("l-1", "borrower", "m-1");
        loan.write("l-1", "openedAt", "2026-10-01T10:00:00Z");
        loan.write("l-1", "loanCopy", "c-1");
        loan.flushAction();

        assertEquals(Set.of("m-1"), loan.read("l-1", "borrower"));
        assertEquals(Set.of("c-1"), loan.read("l-1", "loanCopy"));

        // Returning the loan writes the optional timestamp.
        loan.write("l-1", "returnedAt", "2026-10-04T10:00:00Z");
        Set<String> returned = loan.read("l-1", "returnedAt");
        assertEquals("2026-10-04T10:00:00Z",
                Instant.parse(returned.iterator().next()).toString());
    }

    private static int count(Connection c, String sql) throws Exception {
        try (Statement st = c.createStatement(); ResultSet rs = st.executeQuery(sql)) {
            rs.next();
            return rs.getInt(1);
        }
    }
}
