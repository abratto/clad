package com.example.app.engine;

import org.apache.jena.query.ParameterizedSparqlString;

/**
 * Abstract base for declarative when→then sync rules.
 *
 * <p>Each subclass declares:
 * <ul>
 *   <li>{@link #syncName()} — unique camelCase identifier (used as an RDF
 *       predicate to mark which syncs have already fired on a given trigger).</li>
 *   <li>{@link #whereClause()} — SPARQL WHERE body matching the trigger condition.</li>
 *   <li>{@link #thenBindings()} — SPARQL INSERT body for the new downstream invocation.</li>
 *   <li>{@link #trigger()} — concept IRI + action name + optional outputStatus that
 *       this sync watches; used by {@link SyncDispatcher} to index syncs.</li>
 * </ul>
 *
 * <p>The {@link #execute()} method assembles and executes the full
 * {@code INSERT...WHERE} as a single SPARQL transaction.
 *
 * <p>Hard rule R3: a sync has only final fields and contains no branching
 * domain logic — coordination is expressed in the SPARQL pattern, not in Java.
 */
public abstract class SyncAgent {

    protected final ActionLog actionLog;
    private volatile String cachedSparql;

    protected SyncAgent(ActionLog actionLog) {
        this.actionLog = actionLog;
    }

    /** Unique camelCase name. Used as RDF predicate to record sync firing. */
    public abstract String syncName();

    /** SPARQL WHERE body referencing {@code ?_when_1} and {@code ?_flow}. */
    protected abstract String whereClause();

    /** SPARQL INSERT triples defining {@code ?_then_1} (with blank-node input). */
    protected abstract String thenBindings();

    /** The concept-action-status triple this sync watches. */
    public abstract SyncTrigger trigger();

    /**
     * Returns the IRI of the concept whose invocation this sync writes (parsed
     * from {@link #thenBindings()}). Used by {@link SyncDispatcher} to schedule
     * targeted polls of just the affected concept agents.
     */
    public String targetConceptIri() {
        String text = thenBindings();
        String marker = ":concept <";
        int start = text.indexOf(marker);
        if (start < 0) return null;
        int iriStart = start + marker.length();
        int iriEnd = text.indexOf('>', iriStart);
        if (iriEnd < 0) return null;
        return text.substring(iriStart, iriEnd);
    }

    public void execute() {
        actionLog.update(sparql());
    }

    /** Returns the assembled SPARQL UPDATE; built once and cached. */
    public String sparql() {
        String s = cachedSparql;
        if (s == null) {
            s = parameterizeSparql(assembleSparql());
            cachedSparql = s;
        }
        return s;
    }

    /**
     * Gives subclasses one place to bind string/IRI literals without rebuilding
     * the outer update shape assembled by the base profile.
     */
    protected String parameterizeSparql(String sparql) {
        return sparql;
    }

    protected static String bindLiteral(String sparql, String variableName, String value) {
        ParameterizedSparqlString pss = new ParameterizedSparqlString();
        pss.setCommandText(sparql);
        pss.setLiteral(variableName, value);
        return pss.toString();
    }

    private String assembleSparql() {
        String schema = RdfVocabulary.ACTION_SCHEMA_IRI;
        return "PREFIX : <" + schema + ">\n" +
               "INSERT {\n" +
               "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
               "    ?_then_1 :flow    ?_flow .\n" +
               "    ?_when_1 :" + syncName() + " ?_then_1 .\n" +
               thenBindings() + "\n" +
               "  }\n" +
               "}\n" +
               "WHERE {\n" +
               "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
               "    ?_when_1 :flow    ?_flow .\n" +
               "    FILTER NOT EXISTS { ?_when_1 :" + syncName() + " [] }\n" +
               whereClause() + "\n" +
               "  }\n" +
               "  BIND(IRI(CONCAT(\"" + RdfVocabulary.ACTION_NODE_PREFIX + "\", STRUUID())) AS ?_then_1)\n" +
               "}\n";
    }
}
