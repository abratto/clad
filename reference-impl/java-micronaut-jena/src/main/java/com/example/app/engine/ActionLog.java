package com.example.app.engine;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.apache.jena.rdf.model.Model;

import java.util.List;
import java.util.Map;

/**
 * Facade over {@link Storage}. Delegates all SPARQL and flow-management
 * operations to a pluggable backend. Local (Dataset-based) is the default;
 * remote (RDFLink-based) is used when the {@code fuseki} backend is
 * activated via {@code clad.properties}.
 */
@Singleton
public class ActionLog {

    private final Storage storage;

    public ActionLog() {
        this(new LocalStorage(DatasetFactory.createTxnMem()));
    }

    @Inject
    public ActionLog(Dataset dataset) {
        this(new LocalStorage(dataset));
    }

    /** Used by {@link CladDatasetFactory} for remote backends. */
    ActionLog(Storage storage) {
        this.storage = storage;
    }

    public Dataset dataset() { return storage.dataset(); }

    public void update(String sparqlUpdate) { storage.update(sparqlUpdate); }

    public void updateBatch(List<String> sparqlUpdates) { storage.updateBatch(sparqlUpdates); }

    public Model construct(String sparqlConstruct) { return storage.construct(sparqlConstruct); }

    public boolean ask(String sparqlAsk) { return storage.ask(sparqlAsk); }

    public List<Map<String, String>> select(String sparqlSelect) { return storage.select(sparqlSelect); }

    public void archiveFlow(String flowToken) { storage.archiveFlow(flowToken); }

    public void beginBatch() { storage.beginBatch(); }

    public void flushBatch() { storage.flushBatch(); }

    public void abortBatch() { storage.abortBatch(); }

    public void setArchiveEnabled(boolean enabled) {
        if (storage instanceof LocalStorage ls) ls.setArchiveEnabled(enabled);
    }
}
