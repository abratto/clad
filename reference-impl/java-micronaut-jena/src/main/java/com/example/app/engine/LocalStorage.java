package com.example.app.engine;

import org.apache.jena.query.*;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.update.UpdateExecutionFactory;
import org.apache.jena.update.UpdateFactory;
import org.apache.jena.update.UpdateRequest;

import java.util.*;

/**
 * Dataset-based {@link Storage}. All SPARQL operations execute directly
 * against a Jena {@link Dataset} within transactions.
 */
class LocalStorage implements Storage {

    private final Dataset dataset;
    private final ThreadLocal<List<String>> batched = new ThreadLocal<>();
    private volatile boolean archiveEnabled = true;

    LocalStorage(Dataset dataset) { this.dataset = dataset; }

    @Override public Dataset dataset() { return dataset; }

    void setArchiveEnabled(boolean e) { this.archiveEnabled = e; }

    @Override
    public void update(String sparqlUpdate) {
        List<String> b = batched.get();
        if (b != null) { b.add(sparqlUpdate); return; }
        dataset.begin(ReadWrite.WRITE);
        try {
            UpdateExecutionFactory.create(UpdateFactory.create(sparqlUpdate), dataset).execute();
            dataset.commit();
        } catch (Exception e) { dataset.abort(); throw e; }
        finally { dataset.end(); }
    }

    @Override
    public void updateBatch(List<String> sparqlUpdates) {
        if (sparqlUpdates.isEmpty()) return;
        List<String> b = batched.get();
        if (b != null) { b.addAll(sparqlUpdates); return; }
        dataset.begin(ReadWrite.WRITE);
        try {
            for (String u : sparqlUpdates)
                UpdateExecutionFactory.create(UpdateFactory.create(u), dataset).execute();
            dataset.commit();
        } catch (Exception e) { dataset.abort(); throw e; }
        finally { dataset.end(); }
    }

    @Override
    public Model construct(String sparqlConstruct) {
        dataset.begin(ReadWrite.READ);
        try (QueryExecution qe = QueryExecutionFactory.create(sparqlConstruct, dataset)) {
            return qe.execConstruct(ModelFactory.createDefaultModel());
        } finally { dataset.end(); }
    }

    @Override
    public boolean ask(String sparqlAsk) {
        dataset.begin(ReadWrite.READ);
        try (QueryExecution qe = QueryExecutionFactory.create(sparqlAsk, dataset)) {
            return qe.execAsk();
        } finally { dataset.end(); }
    }

    @Override
    public List<Map<String, String>> select(String sparqlSelect) {
        dataset.begin(ReadWrite.READ);
        try (QueryExecution qe = QueryExecutionFactory.create(sparqlSelect, dataset)) {
            ResultSet rs = qe.execSelect();
            List<Map<String, String>> rows = new ArrayList<>();
            while (rs.hasNext()) {
                var sol = rs.nextSolution();
                Map<String, String> row = new LinkedHashMap<>();
                rs.getResultVars().forEach(col -> {
                    var n = sol.get(col);
                    if (n == null) row.put(col, null);
                    else if (n.isLiteral()) row.put(col, n.asLiteral().getString());
                    else if (n.isResource()) row.put(col, n.asResource().getURI());
                    else row.put(col, n.toString());
                });
                rows.add(row);
            }
            return rows;
        } finally { dataset.end(); }
    }

    @Override
    public void archiveFlow(String flowToken) {
        if (archiveEnabled) doArchive(flowToken); else doDelete(flowToken);
    }

    @Override public void beginBatch() { batched.set(new ArrayList<>()); }

    @Override
    public void flushBatch() {
        List<String> queued = batched.get();
        if (queued == null || queued.isEmpty()) { batched.remove(); return; }
        batched.remove();
        dataset.begin(ReadWrite.WRITE);
        try {
            for (String u : queued)
                UpdateExecutionFactory.create(UpdateFactory.create(u), dataset).execute();
            dataset.commit();
        } catch (Exception e) { dataset.abort(); throw e; }
        finally { dataset.end(); }
    }

    @Override public void abortBatch() { batched.remove(); }

    private void doArchive(String ft) {
        updateBatch(List.of(moveStandard(ft, true), moveStar(ft, true)));
    }
    private void doDelete(String ft) {
        updateBatch(List.of(moveStandard(ft, false), moveStar(ft, false)));
    }

    private static String moveStandard(String ft, boolean archive) {
        String s = RdfVocabulary.ACTION_SCHEMA_IRI;
        String a = RdfVocabulary.ACTION_GRAPH_IRI;
        String arc = RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI;
        String del = "DELETE { GRAPH <" + a + "> { ?s ?p ?o } }\n";
        String ins = archive ? "INSERT { GRAPH <" + arc + "> { ?s ?p ?o } }\n" : "";
        return "PREFIX : <" + s + ">\n" + del + ins
            + "WHERE { GRAPH <" + a + "> { ?a :flow <" + ft + "> ."
            + " { ?a ?p ?o . BIND(?a AS ?s) }"
            + " UNION { ?a :input ?s . ?s ?p ?o } } }\n";
    }
    private static String moveStar(String ft, boolean archive) {
        String s = RdfVocabulary.ACTION_SCHEMA_IRI;
        String a = RdfVocabulary.ACTION_GRAPH_IRI;
        String arc = RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI;
        String del = "DELETE { GRAPH <" + a + "> { << ?a :outcome ?outcome >> ?p ?o } }\n";
        String ins = archive ? "INSERT { GRAPH <" + arc + "> { << ?a :outcome ?outcome >> ?p ?o } }\n" : "";
        return "PREFIX : <" + s + ">\n" + del + ins
            + "WHERE { GRAPH <" + a + "> { ?a :flow <" + ft + "> ."
            + " << ?a :outcome ?outcome >> ?p ?o . } }\n";
    }
}
