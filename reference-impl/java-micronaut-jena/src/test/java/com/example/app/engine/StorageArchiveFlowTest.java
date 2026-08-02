package com.example.app.engine;

import org.apache.jena.fuseki.main.FusekiServer;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class StorageArchiveFlowTest {

    private static FusekiServer fuseki;
    private static String fusekiEndpoint;

    @BeforeAll
    static void startFuseki() {
        Dataset dataset = DatasetFactory.createTxnMem();
        fuseki = FusekiServer.create()
                .port(0)
                .add("/ds", dataset.asDatasetGraph(), true)
                .build();
        fuseki.start();
        fusekiEndpoint = "http://localhost:" + fuseki.getPort() + "/ds";
    }

    @AfterAll
    static void stopFuseki() {
        fuseki.stop();
    }

    @Test
    void localStorageAppliesArchivePolicyToEveryFlowTriple() {
        assertArchivePolicy(new LocalStorage(DatasetFactory.createTxnMem()), "local");
    }

    @Test
    void remoteStorageAppliesArchivePolicyToEveryFlowTriple() {
        assertArchivePolicy(new RemoteStorage(fusekiEndpoint), "remote");
    }

    private static void assertArchivePolicy(Storage storage, String backend) {
        String archivedFlow = "https://clad.dev/flow/archive-" + backend;
        writeCompletedFlow(storage, archivedFlow);
        storage.setArchiveEnabled(true);
        storage.archiveFlow(archivedFlow);

        assertFalse(hasStandardFlow(storage, RdfVocabulary.ACTION_GRAPH_IRI, archivedFlow));
        assertFalse(hasOutcomeAnnotation(storage, RdfVocabulary.ACTION_GRAPH_IRI, archivedFlow));
        assertTrue(hasStandardFlow(storage, RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI, archivedFlow));
        assertTrue(hasOutcomeAnnotation(storage, RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI, archivedFlow));

        String deletedFlow = "https://clad.dev/flow/delete-" + backend;
        writeCompletedFlow(storage, deletedFlow);
        storage.setArchiveEnabled(false);
        storage.archiveFlow(deletedFlow);

        assertFalse(hasStandardFlow(storage, RdfVocabulary.ACTION_GRAPH_IRI, deletedFlow));
        assertFalse(hasOutcomeAnnotation(storage, RdfVocabulary.ACTION_GRAPH_IRI, deletedFlow));
        assertFalse(hasStandardFlow(storage, RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI, deletedFlow));
        assertFalse(hasOutcomeAnnotation(storage, RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI, deletedFlow));
    }

    private static void writeCompletedFlow(Storage storage, String flowToken) {
        String action = flowToken + "/action";
        String input = flowToken + "/input";
        storage.update("""
                PREFIX : <%s>
                INSERT DATA {
                  GRAPH <%s> {
                    <%s> :flow <%s> ; :input <%s> ; :name "request" .
                    <%s> :route "login" .
                    << <%s> :outcome "OK" >> :flow <%s> .
                  }
                }
                """.formatted(
                RdfVocabulary.ACTION_SCHEMA_IRI,
                RdfVocabulary.ACTION_GRAPH_IRI,
                action,
                flowToken,
                input,
                input,
                action,
                flowToken));
    }

    private static boolean hasStandardFlow(Storage storage, String graph, String flowToken) {
        return storage.ask("""
                PREFIX : <%s>
                ASK { GRAPH <%s> { <%s> :flow <%s> } }
                """.formatted(RdfVocabulary.ACTION_SCHEMA_IRI, graph, flowToken + "/action", flowToken));
    }

    private static boolean hasOutcomeAnnotation(Storage storage, String graph, String flowToken) {
        return storage.ask("""
                PREFIX : <%s>
                ASK { GRAPH <%s> { << <%s> :outcome "OK" >> :flow <%s> } }
                """.formatted(RdfVocabulary.ACTION_SCHEMA_IRI, graph, flowToken + "/action", flowToken));
    }
}