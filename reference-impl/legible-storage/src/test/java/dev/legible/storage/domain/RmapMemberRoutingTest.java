package dev.legible.storage.domain;

import dev.legible.engine.InMemoryFactStore;
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
 * Member-qualified routing (maintenance change `member-addressed-routing`):
 * a subtype/partition member is addressed by name, the operation routes to the
 * member's own table, and the in-memory/generic backends ignore the qualifier
 * (their correct semantics — conceptually a concept region is one region).
 */
class RmapMemberRoutingTest {

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
            for (String t : List.of("patient_registry__person", "patient_registry__patient",
                    "organisation__staff", "organisation__manager")) {
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
    @DisplayName("separate mapping: a member write routes to the subtype table")
    void separateMemberWriteRoutesToTheSubtypeTable() throws Exception {
        RmapPostgresFactStore store = store("clinic", "PatientRegistry");
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("PatientRegistry");

        // Base facts (both mandatory on one individual) flush together;
        // the MEMBER write routes to the patient table even though a plain
        // write would route by predicate.
        r.beginAction();
        r.write("pat-1", "registeredAt", "2026-10-06T09:00:00Z");
        r.write("pat-1", "gender", "F");
        r.flushAction();
        r.write("Patient", "pat-1", "insurerName", "ACME");

        assertEquals("ACME",
                cell("patient_registry__patient", "insurer_name", "person = 'pat-1'"),
                "the member write landed in the Patient member table");
        assertEquals(1,
                countRows("patient_registry__person"));
        assertEquals(java.util.Set.of("ACME"),
                r.read("Patient", "pat-1", "insurerName"));
    }

    @Test
    @DisplayName("unknown and absorbed members fail loudly; a member that does not own the predicate fails")
    void memberErrorsAreHonest() throws Exception {
        RmapPostgresFactStore store = store("clinic", "PatientRegistry");
        dev.legible.engine.TransactionalRegion r =
                (dev.legible.engine.TransactionalRegion) store.region("PatientRegistry");

        r.beginAction();
        r.write("pat-1", "registeredAt", "2026-10-06T09:00:00Z");
        r.write("pat-1", "gender", "F");
        r.flushAction();

        var unknown = assertThrows(IllegalArgumentException.class,
                () -> r.write("Astronaut", "pat-1", "insurerName", "X"));
        assertTrue(unknown.getMessage().contains("Astronaut"), unknown.getMessage());
        assertTrue(unknown.getMessage().contains("Patient"), unknown.getMessage());

        // 'Person' names the supertype: no member TABLE named roles-style
        // 'patient_registry__person'... it IS the person table's name, so the
        // supertype routes to its own table — a member-qualified write naming
        // the supertype behaves as the plain write.
        r.write("Person", "pat-1", "gender", "M");
        assertEquals("M", cell("patient_registry__person", "gender", "person = 'pat-1'"));

        // A member that does not own the predicate fails loudly.
        var notOwned = assertThrows(IllegalArgumentException.class,
                () -> r.write("Patient", "pat-1", "gender", "F"));
        assertTrue(notOwned.getMessage().contains("does not own predicate"),
                notOwned.getMessage());

        // Absorbed member: no table of its own.
        String absorbed = """
                partyName: Party -> PartyName -- mandatory
                vatNumber: Employer -> VatNumber -- mandatory
                Employer is a Party -- mapping: absorb
                """;
        RmapModel model = RmapDeriver.deriveModel("Employment", absorbed);
        RmapPostgresFactStore s2 = new RmapPostgresFactStore(dataSource, model.tables());
        s2.createSchema();
        Region e2 = s2.region("Employment");
        var noTable = assertThrows(IllegalArgumentException.class,
                () -> e2.write("Employer", "e-1", "vatNumber", "VAT-1"));
        assertTrue(noTable.getMessage().contains("absorbed"), noTable.getMessage());
    }

    @Test
    @DisplayName("in-memory backend ignores the member (the default semantics)")
    void inMemoryBackendIgnoresTheMember() {
        InMemoryFactStore facts = new InMemoryFactStore();
        Region r = facts.region("PatientRegistry");
        r.write("Patient", "pat-1", "insurerName", "ACME");
        assertEquals(java.util.Set.of("ACME"),
                r.read("Patient", "pat-1", "insurerName"),
                "member-qualified read on the in-memory region");
        assertEquals(java.util.Set.of("ACME"),
                r.read("pat-1", "insurerName"),
                "the member qualifier is ignored — one region, member-agnostic");
    }

    private long countRows(String table) throws Exception {
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement();
             ResultSet rs = st.executeQuery("SELECT count(*) FROM " + table)) {
            rs.next();
            return rs.getLong(1);
        }
    }
}
