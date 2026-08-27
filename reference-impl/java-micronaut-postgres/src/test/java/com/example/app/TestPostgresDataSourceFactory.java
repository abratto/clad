package com.example.app;

import io.micronaut.context.annotation.Factory;
import jakarta.inject.Singleton;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import javax.sql.DataSource;

/**
 * Test-only DataSource backed by a Testcontainers Postgres. Discovered by
 * {@code @MicronautTest} contexts in this profile (concept state is Postgres).
 */
@Factory
public class TestPostgresDataSourceFactory {

    static final PostgreSQLContainer<?> POSTGRES;

    static {
        POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");
        POSTGRES.start();
    }

    @Singleton
    public DataSource dataSource() {
        PGSimpleDataSource dataSource = new PGSimpleDataSource();
        dataSource.setUrl(POSTGRES.getJdbcUrl());
        dataSource.setUser(POSTGRES.getUsername());
        dataSource.setPassword(POSTGRES.getPassword());
        return dataSource;
    }
}
