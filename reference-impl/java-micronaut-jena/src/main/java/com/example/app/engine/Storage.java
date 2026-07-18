package com.example.app.engine;

import org.apache.jena.query.Dataset;
import org.apache.jena.rdf.model.Model;

import java.util.List;
import java.util.Map;

/**
 * Storage abstraction for the action log. Local implementations wrap a
 * Jena {@link Dataset}; remote implementations delegate to an HTTP
 * SPARQL endpoint via {@link org.apache.jena.rdflink.RDFLink}.
 */
public interface Storage {

    void update(String sparqlUpdate);

    void updateBatch(List<String> sparqlUpdates);

    Model construct(String sparqlConstruct);

    boolean ask(String sparqlAsk);

    List<Map<String, String>> select(String sparqlSelect);

    /**
     * Returns the underlying Dataset. Used by {@link SyncDispatcher}
     * for response checking and transaction management. Remote
     * implementations provide a stubbed Dataset for transaction
     * compatibility.
     */
    Dataset dataset();

    /** Archives or deletes all triples for a completed flow token. */
    void archiveFlow(String flowToken);

    /** Begins queuing writes on this thread; flushed atomically. */
    void beginBatch();

    /** Commits all queued writes in a single transaction. */
    void flushBatch();

    /** Discards queued writes. */
    void abortBatch();
}
