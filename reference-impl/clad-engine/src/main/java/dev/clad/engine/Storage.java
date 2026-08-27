package dev.clad.engine;

import org.apache.jena.query.Dataset;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.update.UpdateRequest;

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

    /** Executes a programmatic UpdateRequest directly on the dataset,
     *  bypassing the SPARQL string parser. Required for RDF-star operations
     *  that are legal in Jena'\''s internal representation but rejected by
     *  the strict SPARQL 1.2 parser in UPDATE templates. */
    void update(UpdateRequest request);

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

    /** Deletes all triples for a completed flow token from the action log.
     *  Archival is handled separately by {@link FlowArchiver} — storage
     *  only removes the triples. */
    void archiveFlow(String flowToken);

    /** Begins queuing writes on this thread; flushed atomically. */
    void beginBatch();

    /** Commits all queued writes in a single transaction. */
    void flushBatch();

    /** Discards queued writes. */
    void abortBatch();

    /** Returns true if a batch is currently active (writes are deferred). */
    boolean isBatching();
}
