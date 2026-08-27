package com.example.app.storage;

import dev.clad.engine.FlowArchiver;
import dev.clad.engine.Storage;
import org.apache.jena.query.Dataset;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.update.UpdateRequest;

import java.util.List;
import java.util.Map;

/**
 * In-memory action-log storage that flushes completed flows to the
 * {@link FlowArchiver} (and its sink) before deleting them, then delegates to
 * the wrapped in-memory {@link Storage}.
 *
 * <p>Concept state is <strong>not</strong> held in this store — in this
 * profile it lives in Postgres via JOOQ. Only the transient action log is RDF.
 */
final class FlowArchivingStorage implements Storage {

    private final Storage delegate;
    private FlowArchiver archiver;

    FlowArchivingStorage(Storage delegate) {
        this.delegate = delegate;
    }

    void setArchiver(FlowArchiver archiver) {
        this.archiver = archiver;
    }

    @Override
    public void archiveFlow(String flowToken) {
        if (archiver != null) {
            archiver.archiveFlow(flowToken);
        }
        delegate.archiveFlow(flowToken);
    }

    @Override public void update(String sparqlUpdate) { delegate.update(sparqlUpdate); }
    @Override public void updateBatch(List<String> sparqlUpdates) { delegate.updateBatch(sparqlUpdates); }
    @Override public void update(UpdateRequest request) { delegate.update(request); }
    @Override public Model construct(String sparqlConstruct) { return delegate.construct(sparqlConstruct); }
    @Override public boolean ask(String sparqlAsk) { return delegate.ask(sparqlAsk); }
    @Override public List<Map<String, String>> select(String sparqlSelect) { return delegate.select(sparqlSelect); }
    @Override public Dataset dataset() { return delegate.dataset(); }
    @Override public void beginBatch() { delegate.beginBatch(); }
    @Override public void flushBatch() { delegate.flushBatch(); }
    @Override public void abortBatch() { delegate.abortBatch(); }
    @Override public boolean isBatching() { return delegate.isBatching(); }
}
