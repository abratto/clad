package com.example.app;

import dev.clad.engine.ActionLog;
import dev.clad.engine.CompletionBus;
import dev.clad.engine.FlowManager;
import dev.clad.engine.RdfVocabulary;
import org.flywaydb.core.Flyway;
import org.jooq.DSLContext;
import org.jooq.SQLDialect;
import org.jooq.impl.DSL;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.postgresql.ds.PGSimpleDataSource;
import org.testcontainers.containers.PostgreSQLContainer;

import java.util.List;
import java.util.Map;

import static com.example.app.db.tables.PasswordauthCredentials.PASSWORDAUTH_CREDENTIALS;
import static com.example.app.db.tables.SessionTokens.SESSION_TOKENS;
import static com.example.app.db.tables.Usernames.USERNAMES;

/** Shared fixtures for isolated concept tests backed by a Testcontainers Postgres. */
public abstract class PostgresConceptTestBase {

    private static final PostgreSQLContainer<?> POSTGRES =
            new PostgreSQLContainer<>("postgres:16-alpine");

    protected static DSLContext dsl;

    protected ActionLog log;
    protected CompletionBus bus;
    protected FlowManager flow;
    protected int actionCounter = 0;
    protected String lastActionIri;

    @BeforeAll
    static void startDatabase() {
        POSTGRES.start();
        PGSimpleDataSource dataSource = new PGSimpleDataSource();
        dataSource.setUrl(POSTGRES.getJdbcUrl());
        dataSource.setUser(POSTGRES.getUsername());
        dataSource.setPassword(POSTGRES.getPassword());
        Flyway.configure().dataSource(dataSource).load().migrate();
        dsl = DSL.using(dataSource, SQLDialect.POSTGRES);
    }

    @BeforeEach
    void cleanTablesAndEngine() {
        dsl.deleteFrom(SESSION_TOKENS).execute();
        dsl.deleteFrom(PASSWORDAUTH_CREDENTIALS).execute();
        dsl.deleteFrom(USERNAMES).execute();
        log = new ActionLog();
        bus = new CompletionBus();
        flow = new FlowManager(log, bus);
    }

    protected String freshActionIri(String tag) {
        actionCounter++;
        lastActionIri = RdfVocabulary.ACTION_NODE_PREFIX + tag + "-" + actionCounter;
        return lastActionIri;
    }

    protected void writePendingInvocation(String conceptIri, String actionName, Map<String, String> inputs) {
        String actionIri = freshActionIri(actionName);
        StringBuilder input = new StringBuilder("    _:inp");
        for (Map.Entry<String, String> entry : inputs.entrySet()) {
            input.append(" :").append(entry.getKey())
                    .append(" \"").append(entry.getValue()).append("\" ;");
        }
        String inputBlock = input.substring(0, input.length() - 1) + " .";

        String sparql = "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n"
                + "INSERT DATA {\n"
                + "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n"
                + "    <" + actionIri + "> :concept <" + conceptIri + "> ;\n"
                + "                     :name \"" + actionName + "\" ;\n"
                + "                     :input _:inp ;\n"
                + "                     :flow <" + flow.mintFlowToken() + "> .\n"
                + inputBlock + "\n"
                + "  }\n"
                + "}\n";
        log.update(sparql);
    }

    protected String readOutcome() {
        List<Map<String, String>> rows = log.select(
                "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n"
                + "SELECT ?_outcome WHERE {\n"
                + "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n"
                + "    << <" + lastActionIri + "> :outcome ?_outcome >> :flow ?_flow .\n"
                + "  }\n"
                + "}\n");
        return rows.isEmpty() ? null : rows.get(0).get("_outcome");
    }

    protected String readField(String fieldName) {
        List<Map<String, String>> rows = log.select(
                "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n"
                + "SELECT ?value WHERE {\n"
                + "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n"
                + "    <" + lastActionIri + "> :" + fieldName + " ?value .\n"
                + "  }\n"
                + "}\n");
        return rows.isEmpty() ? null : rows.get(0).get("value");
    }
}
