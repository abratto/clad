package dev.legible.storage;

import dev.legible.engine.Fact;
import dev.legible.engine.Region;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.Statement;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * A reference scheme whose identifier type differs from the entity name
 * ({@code object-type DrinkEntry identified-by EntryId}) must round-trip through
 * the storage SPI: the renamed identity column is the subject, and a written
 * fact reads back with that subject (the {@code identityColumns()} regression).
 */
class RmapReferenceSchemeStoreTest {

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

    @BeforeEach
    void resetTables() throws Exception {
        try (Connection c = dataSource.getConnection();
             Statement st = c.createStatement()) {
            st.execute("DROP TABLE IF EXISTS drink_logging CASCADE");
        }
    }

    @Test
    void factsRoundTripUnderARenamedReferenceScheme() {
        String model = """
                # DrinkLogging — conceptual data model

                ## Machine model

                ```
                object-type DrinkEntry identified-by EntryId
                fact name : DrinkEntry -> DrinkName -- mandatory
                ```
                """;
        RmapPostgresFactStore store = new RmapPostgresFactStore(dataSource,
                RmapDeriver.deriveModelFromDataModel("DrinkLogging", model).tables());
        store.createSchema();

        Region region = store.region("DrinkLogging");
        region.write("e1", "name", "Alice");

        List<Fact> facts = region.facts();
        assertEquals(1, facts.size(), "one fact round-trips: " + facts);
        assertEquals("e1", facts.get(0).subject(),
                "the renamed identity column is the subject");
        assertEquals("name", facts.get(0).predicate());
        assertEquals("Alice", facts.get(0).value());
    }
}
