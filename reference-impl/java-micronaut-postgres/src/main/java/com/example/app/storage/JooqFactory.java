package com.example.app.storage;

import dev.clad.engine.ActionLog;
import dev.clad.engine.FlowArchiver;
import dev.clad.engine.FlowArchiveBuffer;
import dev.clad.engine.FlowArchiveSink;
import dev.clad.engine.LocalStorage;
import dev.clad.engine.LoggerSink;
import io.micronaut.context.annotation.Factory;
import io.micronaut.context.annotation.Primary;
import jakarta.inject.Singleton;
import org.apache.jena.query.DatasetFactory;
import org.flywaydb.core.Flyway;
import org.jooq.DSLContext;
import org.jooq.SQLDialect;
import org.jooq.impl.DSL;

import javax.sql.DataSource;

/**
 * Wires the shared action-log engine (always in-memory) and the Postgres
 * concept-state stack (JOOQ + Flyway) for this profile.
 *
 * <p>The action log stays in-memory RDF; concept state lives in a Postgres
 * schema-per-application. Flyway migrations run before any JOOQ access.
 */
@Factory
public class JooqFactory {

    /** In-memory action log: transient execution state, flushed to the sink on completion. */
    @Singleton
    @Primary
    public ActionLog actionLog(FlowArchiveSink sink, FlowArchiveBuffer buffer) {
        FlowArchivingStorage storage = new FlowArchivingStorage(
                new LocalStorage(DatasetFactory.createTxnMem()));
        ActionLog log = new ActionLog(storage);
        storage.setArchiver(new FlowArchiver(log, sink, buffer));
        return log;
    }

    @Singleton
    FlowArchiveBuffer archiveBuffer() {
        return new FlowArchiveBuffer(100);
    }

    @Singleton
    FlowArchiveSink archiveSink() {
        return new LoggerSink();
    }

    /** Runs Flyway migrations, then exposes a JOOQ {@link DSLContext}. */
    @Singleton
    public DSLContext dslContext(DataSource dataSource) {
        Flyway.configure()
                .dataSource(dataSource)
                .load()
                .migrate();
        return DSL.using(dataSource, SQLDialect.POSTGRES);
    }
}
