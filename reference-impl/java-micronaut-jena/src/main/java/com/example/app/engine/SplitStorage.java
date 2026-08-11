package com.example.app.engine;

import org.apache.jena.query.*;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.update.UpdateRequest;

import java.util.List;
import java.util.Map;

/**
 * Routes SPARQL operations by graph IRI — action log graphs go to an
 * in-memory backend (bounded, fast, cleaned on restart), business graphs
 * go to a durable backend (Fuseki TDB2).
 *
 * <p>This solves unbounded triplestore growth from the action log +
 * archive on TDB2, where DELETEs create tombstones that never free
 * physical space. The in-memory backend reclaims memory immediately
 * on DELETE.
 *
 * <p>Transaction note: the action log and business graphs are NOT in
 * the same transaction. Concept state mutations happen inside
 * {@code processInvocation()}; action log writes happen later in
 * {@code writeCompletion()}. This split matches the existing logical
 * separation.
 */
public class SplitStorage implements Storage {

    /** Action log graphs — transient, in-memory. */
    private static final String ACTIONS_GRAPH = RdfVocabulary.ACTION_GRAPH_IRI;
    private static final String ARCHIVE_GRAPH = RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI;

    private final Storage actionLogBackend;
    private final Storage businessBackend;
    private FlowArchiver archiver;

    public SplitStorage(Storage actionLogBackend, Storage businessBackend) {
        this.actionLogBackend = actionLogBackend;
        this.businessBackend = businessBackend;
        this.archiver = null;
    }

    public void setArchiver(FlowArchiver archiver) {
        this.archiver = archiver;
    }

    private Storage forSparql(String sparql) {
        // Route: action/archive graphs → in-memory, everything else → durable
        if (sparql.contains("<" + ACTIONS_GRAPH + ">")
                || sparql.contains("<" + ARCHIVE_GRAPH + ">")) {
            return actionLogBackend;
        }
        return businessBackend;
    }

    @Override
    public void update(String sparqlUpdate) {
        forSparql(sparqlUpdate).update(sparqlUpdate);
    }

    @Override
    public void updateBatch(List<String> sparqlUpdates) {
        // If any update targets the action log, send all to action log backend.
        // The action log write is always separate from business writes.
        for (String u : sparqlUpdates) {
            if (u.contains(ACTIONS_GRAPH) || u.contains(ARCHIVE_GRAPH)) {
                actionLogBackend.updateBatch(sparqlUpdates);
                return;
            }
        }
        businessBackend.updateBatch(sparqlUpdates);
    }

    @Override
    public void update(UpdateRequest request) {
        businessBackend.update(request);
    }

    @Override
    public Model construct(String sparqlConstruct) {
        return forSparql(sparqlConstruct).construct(sparqlConstruct);
    }

    @Override
    public boolean ask(String sparqlAsk) {
        return forSparql(sparqlAsk).ask(sparqlAsk);
    }

    @Override
    public List<Map<String, String>> select(String sparqlSelect) {
        // Sync queries (SELECT from action log) go to in-memory
        return forSparql(sparqlSelect).select(sparqlSelect);
    }

    @Override
    public Dataset dataset() {
        return actionLogBackend.dataset();
    }

    @Override
    public void archiveFlow(String flowToken) {
        // Flush to log BEFORE deleting — if the flush fails, the
        // FlowArchiveException propagates and the delete is skipped.
        // Triples remain in the in-memory action log for retry.
        if (archiver != null) archiver.archiveFlow(flowToken);
        actionLogBackend.archiveFlow(flowToken);
    }

    @Override
    public void setArchiveEnabled(boolean enabled) {
        actionLogBackend.setArchiveEnabled(enabled);
    }

    @Override
    public void beginBatch() { actionLogBackend.beginBatch(); }

    @Override
    public void flushBatch() { actionLogBackend.flushBatch(); }

    @Override
    public void abortBatch() { actionLogBackend.abortBatch(); }

    @Override
    public boolean isBatching() { return actionLogBackend.isBatching(); }
}
