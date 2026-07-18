package com.example.app.flows;

import com.example.app.engine.ActionLog;
import com.example.app.engine.RemoteStorage;
import org.apache.jena.fuseki.main.FusekiServer;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.apache.jena.rdf.model.Model;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * End-to-end test of the Storage abstraction: start an embedded Fuseki,
 * connect via {@link RemoteStorage} (HTTP SPARQL), and verify CRUD.
 */
class RemoteStorageTest {

    private static FusekiServer server;
    private static RemoteStorage remote;

    @BeforeAll
    static void startFuseki() {
        Dataset ds = DatasetFactory.createTxnMem();
        ds.getDefaultModel().add(
                ds.getDefaultModel().createResource("http://example.org/s"),
                ds.getDefaultModel().createProperty("http://example.org/p"),
                "hello");

        server = FusekiServer.create()
                .port(0)
                .add("/ds", ds.asDatasetGraph(), true)
                .build();
        server.start();
        int port = server.getPort();
        System.out.println("[RemoteStorageTest] fuseki at http://localhost:" + port + "/ds");

        remote = new RemoteStorage("http://localhost:" + port + "/ds");
    }

    @AfterAll
    static void stopFuseki() { server.stop(); }

    @Test
    void askShouldReturnTrue() {
        assertTrue(remote.ask("ASK { ?s ?p ?o }"));
    }

    @Test
    void constructShouldReturnTriples() {
        Model m = remote.construct("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }");
        assertEquals(1, m.size());
    }

    @Test
    void selectShouldReturnRows() {
        List<Map<String, String>> rows = remote.select(
                "SELECT ?s ?p ?o WHERE { ?s ?p ?o }");
        assertEquals(1, rows.size());
        assertEquals("http://example.org/p", rows.get(0).get("p"));
        assertEquals("hello", rows.get(0).get("o"));
    }

    @Test
    void updateShouldInsertAndQuery() {
        remote.update("INSERT DATA { <http://example.org/s2> <http://example.org/p> \"world\" }");
        assertTrue(remote.ask("ASK { <http://example.org/s2> ?p ?o }"));

        List<Map<String, String>> rows = remote.select(
                "SELECT ?o WHERE { <http://example.org/s2> <http://example.org/p> ?o }");
        assertEquals(1, rows.size());
        assertEquals("world", rows.get(0).get("o"));
    }

    @Test
    void batchWriteAndFlush() {
        remote.beginBatch();
        remote.update("INSERT DATA { <http://example.org/b1> <http://example.org/p> \"one\" }");
        remote.update("INSERT DATA { <http://example.org/b2> <http://example.org/p> \"two\" }");
        remote.flushBatch();
        assertTrue(remote.ask("ASK { <http://example.org/b1> ?p \"one\" }"));
        assertTrue(remote.ask("ASK { <http://example.org/b2> ?p \"two\" }"));
    }
}
