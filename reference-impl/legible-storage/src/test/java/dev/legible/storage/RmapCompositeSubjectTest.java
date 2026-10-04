package dev.legible.storage;

import dev.legible.engine.Region;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.Statement;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * A concept whose state has a compound (objectified) subject and a multi-valued
 * fact realises as a table set: the {@code (FirmUri, Service) -> Jurisdiction}
 * fact keys on the component columns directly (no surrogate id, no mapping
 * table), and the {@code FirmUri -> Service} multi-valued fact gets a
 * composite-key child table.
 */
class RmapCompositeSubjectTest {

    private static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:16-alpine");

    private static PGSimpleDataSource dataSource;

    private static final String STATE = """
            firmByClientId: ClientId -> FirmUri                       -- mandatory
            provides: FirmUri -> Service                              -- zero or more
            serviceName: Service -> ServiceName                       -- mandatory
            serviceJurisdiction: (FirmUri, Service) -> Jurisdiction   -- optional
            capabilityStatus: (FirmUri, Service) -> Status            -- optional
            """;

    @BeforeAll
    static void startContainer() {
        POSTGRES.start();
        dataSource = new PGSimpleDataSource();
        dataSource.setUrl(POSTGRES.getJdbcUrl());
        dataSource.setUser(POSTGRES.getUsername());
        dataSource.setPassword(POSTGRES.getPassword());
    }

    @BeforeEach
    void setUp() throws Exception {
        try (Connection c = dataSource.getConnection(); Statement st = c.createStatement()) {
            for (String t : new String[]{"legal_ontology", "legal_ontology__firm_uri",
                    "legal_ontology__service", "legal_ontology__firm_uri_and_service",
                    "legal_ontology__provides"}) {
                st.execute("DROP TABLE IF EXISTS " + t + " CASCADE");
            }
        }
    }

    @Test
    void compositeSubjectIsKeyedByItsPartsAndMultiValuedGetsAChildTable() {
        RmapModel model = RmapDeriver.deriveModel("LegalOntology", STATE);
        var store = new RmapPostgresFactStore(dataSource, model.tables());
        store.createSchema();
        Region region = store.region("LegalOntology");

        // The objectified (firm, service) individual is addressed by its parts.
        region.write(List.of("firm-1", "ChildCustody"), "serviceJurisdiction", "CA");
        region.write(List.of("firm-1", "ChildCustody"), "capabilityStatus", "DELETED");

        assertEquals(Set.of("CA"),
                region.read(List.of("firm-1", "ChildCustody"), "serviceJurisdiction"));
        assertTrue(region.read(List.of("firm-1", "ChildCustody"), "capabilityStatus")
                .contains("DELETED"));

        // A multi-valued fact lives in its own child table.
        region.write("firm-1", "provides", "ChildCustody");
        region.write("firm-1", "provides", "Divorce");
        assertEquals(Set.of("ChildCustody", "Divorce"), region.read("firm-1", "provides"));

        // The composite-key table has the component columns and no surrogate id.
        assertTrue(hasColumn("legal_ontology__firm_uri_and_service", "firm_uri"));
        assertTrue(hasColumn("legal_ontology__firm_uri_and_service", "service"));
        assertTrue(hasColumn("legal_ontology__firm_uri_and_service", "service_jurisdiction"));
    }

    private boolean hasColumn(String table, String column) {
        try (Connection c = dataSource.getConnection();
             Statement st = c.createStatement()) {
            st.executeQuery("SELECT " + column + " FROM " + table + " WHERE false");
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
