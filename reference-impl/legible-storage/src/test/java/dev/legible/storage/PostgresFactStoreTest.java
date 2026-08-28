package dev.legible.storage;

import dev.legible.engine.FactStore;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.sql.Connection;
import java.sql.Statement;

/** {@link PostgresFactStore} satisfies the storage contract and runs the login feature. */
class PostgresFactStoreTest extends StorageContractTest {

    private static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:16-alpine");

    static {
        POSTGRES.start();
        try (Connection c = dataSource().getConnection();
             Statement st = c.createStatement()) {
            st.execute(PostgresFactStore.SCHEMA);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static PGSimpleDataSource dataSource() {
        PGSimpleDataSource ds = new PGSimpleDataSource();
        ds.setUrl(POSTGRES.getJdbcUrl());
        ds.setUser(POSTGRES.getUsername());
        ds.setPassword(POSTGRES.getPassword());
        return ds;
    }

    @Override
    FactStore newStore() {
        return new PostgresFactStore(dataSource());
    }

    @Override
    void reset(FactStore store) {
        try (Connection c = dataSource().getConnection();
             Statement st = c.createStatement()) {
            st.execute("TRUNCATE fact");
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
