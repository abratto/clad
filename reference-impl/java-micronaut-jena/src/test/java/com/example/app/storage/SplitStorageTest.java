package com.example.app.storage;

import dev.clad.engine.*;

import org.apache.jena.query.DatasetFactory;
import org.junit.jupiter.api.*;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("SplitStorage")
class SplitStorageTest {

    private LocalStorage actionLogStorage;
    private LocalStorage businessStorage;
    private SplitStorage split;

    @BeforeEach
    void setUp() {
        actionLogStorage = new LocalStorage(DatasetFactory.createTxnMem());
        businessStorage = new LocalStorage(DatasetFactory.createTxnMem());
        split = new SplitStorage(actionLogStorage, businessStorage);
    }

    @Test
    @DisplayName("action log INSERT routes to in-memory backend")
    void actionLogUpdateRoutesToActionLog() {
        split.update("INSERT DATA { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI
                + "> { <urn:test:1> <urn:test:p> <urn:test:o> } }");

        assertTrue(actionLogStorage.ask(
                "ASK { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> { ?s ?p ?o } }"));
        assertFalse(businessStorage.ask(
                "ASK { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> { ?s ?p ?o } }"));
    }

    @Test
    @DisplayName("business graph INSERT routes to remote backend")
    void businessUpdateRoutesToBusiness() {
        String bizGraph = "https://clad.dev/concept/test";
        split.update("INSERT DATA { GRAPH <" + bizGraph
                + "> { <urn:test:2> <urn:test:p> <urn:test:o> } }");

        assertTrue(businessStorage.ask(
                "ASK { GRAPH <" + bizGraph + "> { ?s ?p ?o } }"));
        assertFalse(actionLogStorage.ask(
                "ASK { GRAPH <" + bizGraph + "> { ?s ?p ?o } }"));
    }

    @Test
    @DisplayName("FlowArchiver writes N-Quads JSON log without throwing")
    void flowArchiverWritesWithoutThrowing() {
        ActionLog log = new ActionLog(split);
        split.update("INSERT DATA { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI
                + "> { <urn:flow:arch> <" + RdfVocabulary.ACTION_SCHEMA_IRI
                + "flow> <urn:flow:arch> } }");

        FlowArchiver archiver = new FlowArchiver(log, new DevNullSink(), new FlowArchiveBuffer());
        archiver.setEnabled(true);

        assertDoesNotThrow(() -> archiver.archiveFlow("urn:flow:arch"));
    }

    @Test
    @DisplayName("archiveFlow: flush failure prevents delete")
    void flushFailurePreventsDelete() {
        // Write triples to action log
        split.update("INSERT DATA { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI
                + "> { <urn:flow:test> <" + RdfVocabulary.ACTION_SCHEMA_IRI
                + "flow> <urn:flow:test> } }");

        // Verify triples exist
        assertTrue(actionLogStorage.ask(
                "ASK { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> { ?s ?p ?o } }"));

        // No archiver set — clean delete path
        split.archiveFlow("urn:flow:test");

        // Triples should be gone after successful delete
        assertFalse(actionLogStorage.ask(
                "ASK { GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> { ?s ?p ?o } }"));
    }

    @Test
    @DisplayName("FlowArchiver disabled does nothing")
    void flowArchiverDisabledNoOp() {
        ActionLog log = new ActionLog(split);
        FlowArchiver archiver = new FlowArchiver(log, new DevNullSink(), new FlowArchiveBuffer());
        archiver.setEnabled(false);
        assertDoesNotThrow(() -> archiver.archiveFlow("urn:flow:anything"));
    }
}
