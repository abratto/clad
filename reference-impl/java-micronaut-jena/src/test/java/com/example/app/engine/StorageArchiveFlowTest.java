package com.example.app.engine;

import org.apache.jena.fuseki.main.FusekiServer;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
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
    void localStorageDeletesEveryFlowTriple() {
        Storage storage = new LocalStorage(DatasetFactory.createTxnMem());
        String flowToken = "https://clad.dev/flow/delete-local";
        writeCompletedFlow(storage, flowToken);
        storage.archiveFlow(flowToken);

        assertFalse(hasStandardFlow(storage, RdfVocabulary.ACTION_GRAPH_IRI, flowToken));
        assertFalse(hasOutcomeAnnotation(storage, RdfVocabulary.ACTION_GRAPH_IRI, flowToken));
    }

    @Test
    void remoteStorageRollsBackEveryOperationInAFailedUpdateRequest() {
        Storage storage = new RemoteStorage(fusekiEndpoint);
        String flowToken = "https://clad.dev/flow/atomic-rollback";
        writeCompletedFlow(storage, flowToken);

        assertThrows(RuntimeException.class, () -> storage.updateBatch(List.of(
                "DELETE { GRAPH <%s> { <%s> ?p ?o } } WHERE { GRAPH <%s> { <%s> ?p ?o } }"
                        .formatted(
                                RdfVocabulary.ACTION_GRAPH_IRI,
                                flowToken + "/action",
                                RdfVocabulary.ACTION_GRAPH_IRI,
                                flowToken + "/action"),
                "LOAD <urn:clad:missing-resource>")));

        assertTrue(hasStandardFlow(storage, RdfVocabulary.ACTION_GRAPH_IRI, flowToken));
        assertTrue(hasOutcomeAnnotation(storage, RdfVocabulary.ACTION_GRAPH_IRI, flowToken));
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
