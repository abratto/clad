package com.example.app.engine;

import jakarta.inject.Singleton;
import org.apache.jena.query.Dataset;
import org.apache.jena.query.DatasetFactory;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.ReadWrite;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.update.UpdateExecutionFactory;
import org.apache.jena.update.UpdateFactory;
import org.apache.jena.update.UpdateRequest;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Jena Dataset wrapper that manages named graphs per concept.
 *
 * <p>Named graphs follow the scheme {@code concept:{name}}, e.g.
 * {@code concept:user}, {@code concept:session}.
 *
 * <p>The global action log is stored in the named graph
 * {@value RdfVocabulary#ACTION_GRAPH_IRI}.
 *
 * <p>This reference profile uses an in-memory transactional Dataset
 * ({@link DatasetFactory#createTxnMem()}). Other profiles can substitute a
 * persistent backend (TDB2, Fuseki, etc.) by replacing this bean.
 */
@Singleton
public class ActionLog {

    private final Dataset dataset;
    private volatile boolean archiveEnabled = true;

    public ActionLog() {
        this(DatasetFactory.createTxnMem());
    }

    /** Constructor used by tests that want to inspect the underlying dataset. */
    public ActionLog(Dataset dataset) {
        this.dataset = dataset;
    }

    /** Returns the underlying Jena {@link Dataset}. */
    public Dataset dataset() {
        return dataset;
    }

    /**
     * Controls whether completed flow triples are archived (default true).
     * When false, {@link #archiveFlow} performs a plain delete instead of
     * a move to the archive graph — useful in production to prevent
     * unbounded heap growth from accumulated flow traces.
     */
    public void setArchiveEnabled(boolean enabled) {
        this.archiveEnabled = enabled;
    }

    /** Executes a SPARQL UPDATE within a write transaction. */
    public void update(String sparqlUpdate) {
        dataset.begin(ReadWrite.WRITE);
        try {
            UpdateRequest request = UpdateFactory.create(sparqlUpdate);
            UpdateExecutionFactory.create(request, dataset).execute();
            dataset.commit();
        } catch (Exception e) {
            dataset.abort();
            throw e;
        } finally {
            dataset.end();
        }
    }

    /**
     * Executes multiple SPARQL UPDATEs within a single write transaction.
     * All updates are applied atomically. An empty list is a no-op.
     */
    public void updateBatch(List<String> sparqlUpdates) {
        if (sparqlUpdates.isEmpty()) return;
        dataset.begin(ReadWrite.WRITE);
        try {
            for (String sparqlUpdate : sparqlUpdates) {
                UpdateRequest request = UpdateFactory.create(sparqlUpdate);
                UpdateExecutionFactory.create(request, dataset).execute();
            }
            dataset.commit();
        } catch (Exception e) {
            dataset.abort();
            throw e;
        } finally {
            dataset.end();
        }
    }

    /** Executes a SPARQL CONSTRUCT within a read transaction. */
    public Model construct(String sparqlConstruct) {
        dataset.begin(ReadWrite.READ);
        try (QueryExecution qexec = QueryExecutionFactory.create(sparqlConstruct, dataset)) {
            return qexec.execConstruct(ModelFactory.createDefaultModel());
        } finally {
            dataset.end();
        }
    }

    /** Executes a SPARQL ASK within a read transaction. */
    public boolean ask(String sparqlAsk) {
        dataset.begin(ReadWrite.READ);
        try (QueryExecution qexec = QueryExecutionFactory.create(sparqlAsk, dataset)) {
            return qexec.execAsk();
        } finally {
            dataset.end();
        }
    }

    /**
     * Executes a SPARQL SELECT and returns each row as a map of variable name
     * to lexical value (literals as their string form, IRIs as their full URI).
     */
    public List<Map<String, String>> select(String sparqlSelect) {
        dataset.begin(ReadWrite.READ);
        try (QueryExecution qexec = QueryExecutionFactory.create(sparqlSelect, dataset)) {
            ResultSet results = qexec.execSelect();
            List<Map<String, String>> rows = new ArrayList<>();
            while (results.hasNext()) {
                var sol = results.nextSolution();
                Map<String, String> row = new LinkedHashMap<>();
                results.getResultVars().forEach(col -> {
                    var node = sol.get(col);
                    if (node == null) {
                        row.put(col, null);
                    } else if (node.isLiteral()) {
                        row.put(col, node.asLiteral().getString());
                    } else if (node.isResource()) {
                        row.put(col, node.asResource().getURI());
                    } else {
                        row.put(col, node.toString());
                    }
                });
                rows.add(row);
            }
            return rows;
        } finally {
            dataset.end();
        }
    }

    /**
     * Removes all triples belonging to a completed flow from the active
     * action graph. When archiving is enabled, the triples are moved to the
     * archive graph for Stage 05 verification; when disabled, they are
     * simply deleted.
     */
    public void archiveFlow(String flowToken) {
        if (archiveEnabled) {
            doArchiveFlow(flowToken);
        } else {
            doDeleteFlow(flowToken);
        }
    }

    private void doArchiveFlow(String flowToken) {
        String schema = RdfVocabulary.ACTION_SCHEMA_IRI;
        String active = RdfVocabulary.ACTION_GRAPH_IRI;
        String archive = RdfVocabulary.ACTION_ARCHIVE_GRAPH_IRI;

        String moveStandard =
            "PREFIX : <" + schema + ">\n" +
            "DELETE { GRAPH <" + active + "> { ?s ?p ?o } }\n" +
            "INSERT { GRAPH <" + archive + "> { ?s ?p ?o } }\n" +
            "WHERE  { GRAPH <" + active + "> {\n" +
            "  ?a :flow <" + flowToken + "> .\n" +
            "  { ?a ?p ?o . BIND(?a AS ?s) }\n" +
            "  UNION { ?a :input ?s . ?s ?p ?o }\n" +
            "} }\n";

        String moveStar =
            "PREFIX : <" + schema + ">\n" +
            "DELETE { GRAPH <" + active + "> { << ?a :outcome ?outcome >> ?p ?o } }\n" +
            "INSERT { GRAPH <" + archive + "> { << ?a :outcome ?outcome >> ?p ?o } }\n" +
            "WHERE  { GRAPH <" + active + "> {\n" +
            "  ?a :flow <" + flowToken + "> .\n" +
            "  << ?a :outcome ?outcome >> ?p ?o .\n" +
            "} }\n";

        updateBatch(List.of(moveStandard, moveStar));
    }

    private void doDeleteFlow(String flowToken) {
        String schema = RdfVocabulary.ACTION_SCHEMA_IRI;
        String active = RdfVocabulary.ACTION_GRAPH_IRI;

        String deleteStandard =
            "PREFIX : <" + schema + ">\n" +
            "DELETE { GRAPH <" + active + "> { ?s ?p ?o } }\n" +
            "WHERE  { GRAPH <" + active + "> {\n" +
            "  ?a :flow <" + flowToken + "> .\n" +
            "  { ?a ?p ?o . BIND(?a AS ?s) }\n" +
            "  UNION { ?a :input ?s . ?s ?p ?o }\n" +
            "} }\n";

        String deleteStar =
            "PREFIX : <" + schema + ">\n" +
            "DELETE { GRAPH <" + active + "> { << ?a :outcome ?outcome >> ?p ?o } }\n" +
            "WHERE  { GRAPH <" + active + "> {\n" +
            "  ?a :flow <" + flowToken + "> .\n" +
            "  << ?a :outcome ?outcome >> ?p ?o .\n" +
            "} }\n";

        updateBatch(List.of(deleteStandard, deleteStar));
    }
}
