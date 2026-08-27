package com.example.app.storage;

import dev.clad.engine.*;

import org.apache.jena.query.DatasetFactory;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.wait.strategy.Wait;
import org.testcontainers.utility.MountableFile;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Opt-in end-to-end test of the remote storage path against a genuinely
 * separate Apache Jena Fuseki (Jena 6, TDB2) running in a container — the
 * same image and config used by {@code docker-compose.yml}.
 *
 * <p>The embedded {@link RemoteStorageTest} uses an in-process Fuseki on the
 * <em>same</em> Jena version as the app, so its parser is lenient in the same
 * ways. This test catches the divergence the embedded one cannot (CLAD R21:
 * SPARQL accepted locally but rejected by a strict remote triplestore over
 * HTTP).
 *
 * <p>Tagged {@code docker} and excluded from the default {@code mvn test}.
 * Run with {@code mvn test -Pdocker} (Docker required).
 */
@Tag("docker")
class RemoteStorageContainerTest {

    private static final String QUERY_PATH = "/clad/query";
    private static final String UPDATE_PATH = "/clad/update";

    static final GenericContainer<?> FUSEKI = new GenericContainer<>("conceptkernel/jena-fuseki:latest")
            .withExposedPorts(3030)
            // The repo's own Fuseki config — creates the /clad TDB2 dataset.
            .withCopyFileToContainer(
                    MountableFile.forClasspathResource("/fuseki/config.ttl"),
                    "/fuseki/run/configuration/clad.ttl")
            // macOS host can't chown to the image UID; run as root (matches compose).
            .withCreateContainerCmdModifier(cmd -> cmd.withUser("0:0"))
            .waitingFor(Wait.forHttp("/$/ping").forPort(3030).forStatusCode(200));

    static {
        FUSEKI.start();
    }

    private static String endpoint(String path) {
        return "http://localhost:" + FUSEKI.getMappedPort(3030) + path;
    }

    /** Split query/update endpoints — mirrors docker-compose (CONSTRUCT on /update 400s). */
    private static RemoteStorage remote() {
        return new RemoteStorage(endpoint(QUERY_PATH), endpoint(UPDATE_PATH));
    }

    @Test
    void remoteStorageCrudRoundTrip() {
        RemoteStorage remote = remote();

        remote.update("INSERT DATA { <http://example.org/r1> <http://example.org/rp> \"remote\" }");
        assertTrue(remote.ask("ASK { <http://example.org/r1> <http://example.org/rp> \"remote\" }"));
        assertEquals(1, remote.construct(
                "CONSTRUCT { <http://example.org/r1> ?p ?o } WHERE { <http://example.org/r1> ?p ?o }").size());
        assertEquals(1, remote.select("SELECT ?o WHERE { <http://example.org/r1> <http://example.org/rp> ?o }").size());
    }

    @Test
    void splitStorageRoutesBusinessGraphsToRemote() {
        // Action log → in-memory; business graph → remote Fuseki.
        SplitStorage split = new SplitStorage(
                new LocalStorage(DatasetFactory.createTxnMem()),
                remote());

        String businessGraph = RdfVocabulary.conceptGraph("user");
        split.update("INSERT DATA { GRAPH <" + businessGraph
                + "> { <http://example.org/u1> <http://example.org/uname> \"ada\" } }");

        // The business write must be visible on the remote endpoint.
        RemoteStorage probe = remote();
        assertTrue(probe.ask("ASK { GRAPH <" + businessGraph
                + "> { <http://example.org/u1> <http://example.org/uname> \"ada\" } }"));

        // The action-log write must NOT leak to remote (stays in-memory).
        String actionGraph = RdfVocabulary.ACTION_GRAPH_IRI;
        split.update("INSERT DATA { GRAPH <" + actionGraph
                + "> { <http://example.org/a1> <http://example.org/ap> \"in-memory\" } }");
        assertFalse(probe.ask("ASK { GRAPH <" + actionGraph
                + "> { <http://example.org/a1> <http://example.org/ap> \"in-memory\" } }"));
        assertTrue(split.ask("ASK { GRAPH <" + actionGraph
                + "> { <http://example.org/a1> <http://example.org/ap> \"in-memory\" } }"));
    }

    @Test
    void actionLogWrapperRoundTripsThroughSplitStorage() {
        SplitStorage split = new SplitStorage(
                new LocalStorage(DatasetFactory.createTxnMem()),
                remote());
        ActionLog log = new ActionLog(split);

        log.beginBatch();
        log.update("INSERT DATA { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI
                + "> { <http://example.org/b1> <http://example.org/bp> \"batched\" } }");
        log.flushBatch();

        List<Map<String, String>> rows = log.select(
                "SELECT ?o WHERE { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI
                + "> { <http://example.org/b1> <http://example.org/bp> ?o } }");
        assertEquals(1, rows.size());
        assertEquals("batched", rows.get(0).get("o"));
    }
}
