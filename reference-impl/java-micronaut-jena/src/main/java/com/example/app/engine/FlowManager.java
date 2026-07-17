package com.example.app.engine;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.apache.jena.graph.NodeFactory;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.ResourceFactory;
import org.apache.jena.riot.out.NodeFmtLib;
import org.apache.jena.riot.system.PrefixMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Mints flow tokens and writes root Web/request action nodes to the RDF store.
 *
 * <p>Every HTTP request handled by the Web controller starts here. The
 * {@link #rootAction(String, Map)} method:
 * <ol>
 *   <li>Mints a UUID-based flow token IRI.</li>
 *   <li>Creates a unique action node IRI.</li>
 *   <li>Writes the Web/request RDF triples to the action log named graph.</li>
 *   <li>Writes a self-outcome (Web/request always succeeds at the receive step).</li>
 *   <li>Signals the {@link CompletionBus} so awaiting syncs are scheduled.</li>
 *   <li>Returns an {@link ActionRecord} representing the root action.</li>
 * </ol>
 */
@Singleton
public class FlowManager {

    /** The IRI used to identify the Web concept in :concept triples. */
    public static final String WEB_CONCEPT_IRI = "https://clad.dev/concept/web";

    private static final String SCHEMA = RdfVocabulary.ACTION_SCHEMA_IRI;
    private static final String INDENT_IRI = "    <";
    private static final String SUFFIX_SEMI = "> ;\n";
    private static final Logger LOG = LoggerFactory.getLogger(FlowManager.class);

    private final ActionLog actionLog;
    private final CompletionBus completionBus;

    @Inject
    public FlowManager(ActionLog actionLog, CompletionBus completionBus) {
        this.actionLog = actionLog;
        this.completionBus = completionBus;
    }

    /** Mints a new UUID-based flow token IRI. */
    public String mintFlowToken() {
        return RdfVocabulary.FLOW_TOKEN_PREFIX + UUID.randomUUID();
    }

    /**
     * Creates a root Web/request action for the given route and request parameters,
     * writes its RDF representation to the action log, and returns the resulting
     * {@link ActionRecord}.
     */
    public ActionRecord rootAction(String route, Map<String, String> requestParams) {
        String flowToken = mintFlowToken();
        LOG.debug("[flow] {} → {}", route, flowToken);
        String actionIri = RdfVocabulary.ACTION_NODE_PREFIX + UUID.randomUUID();
        String inputIri = actionIri + "/input";

        StringBuilder sparql = new StringBuilder();
        sparql.append("PREFIX : <").append(SCHEMA).append(">\n");
        sparql.append("INSERT DATA {\n");
        sparql.append("  GRAPH <").append(RdfVocabulary.ACTION_GRAPH_IRI).append("> {\n");
        sparql.append("    <").append(actionIri).append("> :concept <").append(WEB_CONCEPT_IRI).append(SUFFIX_SEMI);
        sparql.append("         :name \"request\" ;\n");
        sparql.append("         :input <").append(inputIri).append(SUFFIX_SEMI);
        sparql.append("         :flow <").append(flowToken).append("> .\n");
        sparql.append("    <").append(actionIri).append("> :outcome \"received\" .\n");
        sparql.append(INDENT_IRI).append(inputIri).append("> :route ")
              .append(NodeFmtLib.str(NodeFactory.createLiteralString(route), (PrefixMap) null)).append(" .\n");
        for (Map.Entry<String, String> entry : requestParams.entrySet()) {
            sparql.append(INDENT_IRI).append(inputIri).append("> :")
                  .append(entry.getKey()).append(" ")
                  .append(NodeFmtLib.str(NodeFactory.createLiteralString(entry.getValue()), (PrefixMap) null)).append(" .\n");
        }
        sparql.append("  }\n");
        sparql.append("}\n");

        actionLog.update(sparql.toString());
        completionBus.signal(WEB_CONCEPT_IRI);

        Map<String, RDFNode> bindings = new HashMap<>();
        bindings.put("route", ResourceFactory.createStringLiteral(route));
        for (Map.Entry<String, String> entry : requestParams.entrySet()) {
            bindings.put(entry.getKey(), ResourceFactory.createStringLiteral(entry.getValue()));
        }

        return new ActionRecord(
                actionIri,
                flowToken,
                WEB_CONCEPT_IRI,
                "request",
                Collections.unmodifiableMap(bindings)
        );
    }
}
