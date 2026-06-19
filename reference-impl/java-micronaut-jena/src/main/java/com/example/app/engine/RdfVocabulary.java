package com.example.app.engine;

/**
 * Central RDF vocabulary constants for the CLAD action log.
 * Schema prefix: {@code https://clad.dev/schema#}
 */
public final class RdfVocabulary {

    /** Base IRI for the action log schema. */
    public static final String ACTION_SCHEMA_IRI = "https://clad.dev/schema#";

    /** The :actions predicate (legacy — migrated to RDF-star; no longer in use). */
    public static final String ACTIONS = ACTION_SCHEMA_IRI + "actions";

    /** The :concept predicate — links an action node to its concept IRI. */
    public static final String CONCEPT = ACTION_SCHEMA_IRI + "concept";

    /** The :name predicate — the action name string. */
    public static final String NAME = ACTION_SCHEMA_IRI + "name";

    /** The :input predicate — links an action node to its input blank node. */
    public static final String INPUT = ACTION_SCHEMA_IRI + "input";

    /** The :output predicate (legacy — migrated to :outcome with RDF-star annotation; no longer in use). */
    public static final String OUTPUT = ACTION_SCHEMA_IRI + "output";

    /** The :flow predicate — the flow token IRI shared across a causal chain. */
    public static final String FLOW = ACTION_SCHEMA_IRI + "flow";

    /** The :status predicate — outcome status on output nodes. */
    public static final String STATUS = ACTION_SCHEMA_IRI + "status";

    /** The named graph IRI for the global action log. */
    public static final String ACTION_GRAPH_IRI = "https://clad.dev/actions";

    /** The named graph IRI for the completed-flow archive. */
    public static final String ACTION_ARCHIVE_GRAPH_IRI = "https://clad.dev/actions/archive";

    /** Base IRI for fresh action nodes. */
    public static final String ACTION_NODE_PREFIX = "https://clad.dev/action/";

    /** Base IRI for flow tokens. */
    public static final String FLOW_TOKEN_PREFIX = "https://clad.dev/flow/";

    /**
     * Returns the named graph IRI for a concept's state.
     *
     * @param conceptName the lowercase concept name (e.g. "user", "session")
     * @return the named graph IRI string, e.g. {@code "concept:user"}
     */
    public static String conceptGraph(String conceptName) {
        return "concept:" + conceptName;
    }

    private RdfVocabulary() {}
}
