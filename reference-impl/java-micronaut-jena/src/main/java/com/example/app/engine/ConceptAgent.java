package com.example.app.engine;

import org.apache.jena.query.ParameterizedSparqlString;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.NodeIterator;
import org.apache.jena.rdf.model.Property;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.Resource;
import org.apache.jena.rdf.model.ResourceFactory;
import org.apache.jena.rdf.model.StmtIterator;
import org.apache.jena.riot.out.NodeFmtLib;
import org.apache.jena.riot.system.PrefixMap;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
/**
 * Abstract base for concept agents.
 *
 * <p>A concept agent:
 * <ol>
 *   <li>Polls the action log with a SPARQL CONSTRUCT to find pending invocations.</li>
 *   <li>Dispatches each invocation to {@link #processInvocation(ActionRecord)}.</li>
 *   <li>Writes completion triples back to the action log via
 *       {@link #writeCompletion}, {@link #writeRefusal}, or {@link #writeError}.</li>
 * </ol>
 *
 * <p>Hard rule R1: a concept agent does not import or call any sibling concept's
 * code. State lives in this concept's named graph
 * ({@link RdfVocabulary#conceptGraph(String)}); coordination happens only through
 * the action log.
 */
public abstract class ConceptAgent {

    protected final ActionLog actionLog;
    private final CompletionBus completionBus;

    protected ConceptAgent(ActionLog actionLog, CompletionBus completionBus) {
        this.actionLog = actionLog;
        this.completionBus = completionBus;
    }

    /** The IRI of this concept, e.g. {@code "https://clad.dev/concept/user"}. */
    protected abstract String conceptIRI();

    /** Named graph holding action nodes for this concept. Defaults to the global log. */
    protected String actionGraphIRI() {
        return RdfVocabulary.ACTION_GRAPH_IRI;
    }

    /**
     * Processes a single pending invocation. Implementations must call either
     * {@link #writeCompletion} or {@link #writeError} before returning.
     */
    protected abstract void processInvocation(ActionRecord invocation);

    /**
     * Polls all action names handled by this concept agent.
     * Called by {@link SyncDispatcher} on each dispatch tick.
     */
    public abstract void pollAll();

    /** Polls for pending invocations of one action name and processes each. */
    public void pollAndProcess(String actionName) {
        for (ActionRecord invocation : findPendingInvocations(actionName)) {
            processInvocation(invocation);
        }
    }

    protected List<ActionRecord> findPendingInvocations(String actionName) {
        Model model = actionLog.construct(buildPendingQuery(actionName));
        return parseInvocations(model, actionName);
    }

    private String buildPendingQuery(String actionName) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("", RdfVocabulary.ACTION_SCHEMA_IRI);
        pss.setCommandText("""
                CONSTRUCT {
                  ?_action :input ?input ; :flow ?_flow .
                  ?input ?inputPred ?inputVal .
                }
                WHERE {
                    GRAPH ?actionGraph {
                        ?_action :concept  ?concept ;
                                 :name     ?actionName ;
                                 :input    ?input ;
                                 :flow     ?_flow .
                        OPTIONAL { ?input ?inputPred ?inputVal . }
                        FILTER NOT EXISTS { ?_action :outcome ?_any_outcome }
                    }
                }
                """);
        pss.setIri("actionGraph", actionGraphIRI());
        pss.setIri("concept", conceptIRI());
        pss.setLiteral("actionName", actionName);
        return pss.toString();
    }

    private List<ActionRecord> parseInvocations(Model model, String actionName) {
        List<ActionRecord> results = new ArrayList<>();
        Property inputProp = ResourceFactory.createProperty(RdfVocabulary.INPUT);
        Property flowProp = ResourceFactory.createProperty(RdfVocabulary.FLOW);

        StmtIterator it = model.listStatements(null, inputProp, (RDFNode) null);
        while (it.hasNext()) {
            var stmt = it.nextStatement();
            Resource actionResource = stmt.getSubject();
            String actionIri = actionResource.getURI();
            RDFNode inputNode = stmt.getObject();

            String flowToken = null;
            NodeIterator flowIt = model.listObjectsOfProperty(actionResource, flowProp);
            if (flowIt.hasNext()) {
                RDFNode flowNode = flowIt.next();
                if (flowNode.isResource()) {
                    flowToken = flowNode.asResource().getURI();
                }
            }

            Map<String, RDFNode> bindings = new HashMap<>();
            if (inputNode != null && inputNode.isResource()) {
                StmtIterator inputStmts = model.listStatements(inputNode.asResource(), null, (RDFNode) null);
                while (inputStmts.hasNext()) {
                    var inputStmt = inputStmts.nextStatement();
                    String localName = inputStmt.getPredicate().getLocalName();
                    bindings.put(localName, inputStmt.getObject());
                }
            }

            results.add(new ActionRecord(actionIri, flowToken, conceptIRI(), actionName, bindings));
        }
        return results;
    }

    /** Writes completion (output) triples and signals the bus. */
    protected void writeCompletion(ActionRecord invocation, Map<String, RDFNode> output) {
        StringBuilder sparql = new StringBuilder();
        sparql.append("PREFIX : <").append(RdfVocabulary.ACTION_SCHEMA_IRI).append(">\n");
        sparql.append("INSERT DATA {\n");
        sparql.append("  GRAPH <").append(actionGraphIRI()).append("> {\n");
        RDFNode outcomeNode = output.get("outcome");
        sparql.append("    <").append(invocation.actionIri()).append("> :outcome ")
              .append(NodeFmtLib.str(outcomeNode.asNode(), (PrefixMap) null))
              .append(" .\n");
        for (Map.Entry<String, RDFNode> entry : output.entrySet()) {
            // Skip plain :outcome — already written above to prevent reprocessing.
            // RDF-star annotation below carries the outcome for sync matching.
            if ("outcome".equals(entry.getKey())) continue;
            sparql.append("    <").append(invocation.actionIri()).append("> :")
                  .append(entry.getKey()).append(" ")
                  .append(NodeFmtLib.str(entry.getValue().asNode(), (PrefixMap) null))
                  .append(" .\n");
        }
        sparql.append("    << <").append(invocation.actionIri()).append("> :outcome ")
              .append(NodeFmtLib.str(output.get("outcome").asNode(), (PrefixMap) null))
              .append(" >> :flow <").append(invocation.flowToken()).append("> .\n");
        sparql.append("  }\n");
        sparql.append("}\n");
        actionLog.update(sparql.toString());
        completionBus.signal(conceptIRI());
    }

    /**
     * Signals the {@link CompletionBus} that this concept completed an action.
     * Use only when writing custom output triples directly via
     * {@link ActionLog#update}; {@link #writeCompletion}/{@link #writeError}
     * already signal automatically.
     */
    protected void signalCompletion() {
        completionBus.signal(conceptIRI());
    }

    /**
     * Writes a refusal — the action's precondition failed, so the concept
     * refused to execute it. No state change occurred. Writes a plain
     * {@code :outcome "refused"} triple (for dedup via
     * {@link #findPendingInvocations}), an optional {@code :refusalReason},
     * and an RDF-star annotation so syncs can match on the refusal.
     */
    protected void writeRefusal(ActionRecord invocation, String reason) {
        StringBuilder sparql = new StringBuilder();
        sparql.append("PREFIX : <").append(RdfVocabulary.ACTION_SCHEMA_IRI).append(">\n");
        sparql.append("INSERT DATA {\n");
        sparql.append("  GRAPH <").append(actionGraphIRI()).append("> {\n");
        sparql.append("    <").append(invocation.actionIri()).append("> :outcome \"refused\"");
        if (reason != null && !reason.isBlank()) {
            sparql.append(" ;\n");
            sparql.append("         :refusalReason ")
                  .append(NodeFmtLib.str(ResourceFactory.createStringLiteral(reason).asNode(), (PrefixMap) null));
        }
        sparql.append(" .\n");
        sparql.append("    << <").append(invocation.actionIri()).append("> :outcome \"refused\" >>");
        sparql.append(" :flow <").append(invocation.flowToken()).append("> .\n");
        sparql.append("  }\n");
        sparql.append("}\n");
        actionLog.update(sparql.toString());
        completionBus.signal(conceptIRI());
    }

    /** Writes an error output for the given invocation. */
    protected void writeError(ActionRecord invocation, String message) {
        StringBuilder sparql = new StringBuilder();
        sparql.append("PREFIX : <").append(RdfVocabulary.ACTION_SCHEMA_IRI).append(">\n");
        sparql.append("INSERT DATA {\n");
        sparql.append("  GRAPH <").append(actionGraphIRI()).append("> {\n");
        sparql.append("    <").append(invocation.actionIri()).append("> :outcome \"error\" ;\n");
        sparql.append("         :status \"error\" ;\n");
        sparql.append("         :message ")
              .append(NodeFmtLib.str(ResourceFactory.createStringLiteral(message).asNode(), (PrefixMap) null))
              .append(" .\n");
        sparql.append("    << <").append(invocation.actionIri()).append("> :outcome \"error\" >>");
        sparql.append(" :flow <").append(invocation.flowToken()).append("> .\n");
        sparql.append("  }\n");
        sparql.append("}\n");
        actionLog.update(sparql.toString());
        completionBus.signal(conceptIRI());
    }
}
