package com.example.app.engine.predicate;

import com.example.app.engine.ActionLog;
import com.example.app.engine.ActionRecord;
import com.example.app.engine.CompletionBus;
import com.example.app.engine.ConceptAgent;
import com.example.app.engine.RdfVocabulary;
import com.example.app.engine.SyncAgent;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.riot.out.NodeFmtLib;
import org.apache.jena.riot.system.PrefixMap;

import java.util.List;
import java.util.Map;

/**
 * Concept agent base class for the predicate engine.
 *
 * <h3>Key behavioral difference from the reference engine</h3>
 *
 * <p>In the reference engine, any outcome can be committed. The dispatcher
 * simply won't fire any syncs for an unmatched outcome. The action quietly
 * succeeds with no follow-through, leaving the flow chain hanging.
 *
 * <p>In the predicate engine, {@code writeCompletion} evaluates which syncs
 * match the proposed outcome BEFORE writing anything. If no sync matches
 * and the action is not Web/respond, the completion is rejected before any
 * state is modified. The concept is informed that its outcome has no
 * valid path through the system.
 *
 * <p>This implements the paper's predicate model: synchronizations are
 * logical constraints over the combined action space. An action is only
 * valid if at least one synchronization predicate is satisfied by its
 * outcome. No unmatched actions can exist in the system.
 *
 * <p>The composite write (completion + sync invocations) is a single Jena
 * transaction via {@link ActionLog#beginBatch}/{@link ActionLog#flushBatch}.
 * A reader never sees A's completion without B's invocation — the entire
 * composite transition commits or rolls back atomically.
 */
public abstract class PredicateConceptAgent extends ConceptAgent {

    private static final String WEB_CONCEPT_IRI = "https://clad.dev/concept/web";
    private static final PredicateSyncDispatcher NOOP = null;

    protected final PredicateSyncDispatcher dispatcher;

    /**
     * Production constructor — concept participates in full predicate evaluation.
     * Every outcome must have a matching sync unless it's Web/respond.
     */
    protected PredicateConceptAgent(
            ActionLog actionLog,
            CompletionBus completionBus,
            PredicateSyncDispatcher dispatcher) {
        super(actionLog, completionBus);
        this.dispatcher = dispatcher;
    }

    /**
     * Test constructor — predicate evaluation is bypassed. Use this for
     * isolated concept tests that verify internal logic without requiring
     * syncs to be registered. The concept commits outcomes normally without
     * checking whether syncs match.
     *
     * <p>Concept tests should NOT register syncs just to make the predicate
     * engine happy — that couples the test to the sync configuration when
     * the test only cares about the concept's internal behavior.
     */
    protected PredicateConceptAgent(
            ActionLog actionLog,
            CompletionBus completionBus) {
        super(actionLog, completionBus);
        this.dispatcher = null;
    }

    /**
     * Writes a completion with predicate enforcement.
     *
     * <ol>
     *   <li>Evaluates which syncs match this outcome.</li>
     *   <li>If no sync matches and this is not a Web/respond action,
     *       throws {@link SyncEvaluationException}.</li>
     *   <li>If syncs match, writes the completion, then fires each
     *       matching sync sequentially.</li>
     * </ol>
     */
    @Override
    protected void writeCompletion(ActionRecord invocation, Map<String, RDFNode> output) {
        RDFNode outcomeNode = output.get("outcome");
        if (outcomeNode == null) {
            throw new SyncEvaluationException(
                    "writeCompletion called without an 'outcome' field");
        }
        String outcome = outcomeNode.asLiteral().getString();

        boolean isRespondAction = WEB_CONCEPT_IRI.equals(invocation.conceptIri())
                && "respond".equals(invocation.actionName());

        // Test mode: dispatcher is null — skip predicate evaluation.
        // Used by isolated concept tests that verify internal logic without
        // registering syncs. Outcomes commit normally without sync matching.
        if (dispatcher == null) {
            writeCompletionSparql(invocation, output);
            signalCompletion();
            return;
        }

        List<SyncAgent> matchingSyncs = dispatcher.evaluateSyncs(
                invocation.conceptIri(), invocation.actionName(), outcome);

        if (matchingSyncs.isEmpty() && !isRespondAction) {
            throw new SyncEvaluationException(
                    "No sync matches outcome '" + outcome
                    + "' for " + invocation.conceptIri()
                    + "/" + invocation.actionName()
                    + ". Add a sync rule to handle this outcome.");
        }

        // Atomic composite write: batch all SPARQL into one transaction.
        // If the dispatcher already started a batch (outer batch holds concept
        // state mutations), merge into it instead of starting a new one.
        boolean outerBatch = actionLog.isBatching();
        if (!outerBatch) actionLog.beginBatch();
        try {
            writeCompletionSparql(invocation, output);
            for (SyncAgent sync : matchingSyncs) {
                sync.execute();
            }
            if (!outerBatch) actionLog.flushBatch();
        } catch (Exception e) {
            if (!outerBatch) actionLog.abortBatch();
            throw new SyncEvaluationException(
                    "Atomic composite write failed for " + invocation.conceptIri()
                    + "/" + invocation.actionName() + "[" + outcome + "]: "
                    + e.getMessage(), e);
        }

        // Flow archival: when Web/respond completes, flush the flow's triples
        // to the archive sink and delete them from the in-memory action log
        // to prevent unbounded growth.
        if (isRespondAction && invocation.flowToken() != null) {
            actionLog.archiveFlow(invocation.flowToken());
        }
    }

    private void writeCompletionSparql(ActionRecord invocation, Map<String, RDFNode> output) {
        StringBuilder sparql = new StringBuilder();
        sparql.append("PREFIX : <").append(RdfVocabulary.ACTION_SCHEMA_IRI).append(">\n");
        sparql.append("INSERT DATA {\n");
        sparql.append("  GRAPH <").append(actionGraphIRI()).append("> {\n");

        RDFNode outcomeNode = output.get("outcome");
        sparql.append("    <").append(invocation.actionIri()).append("> :outcome ")
              .append(NodeFmtLib.str(outcomeNode.asNode(), (PrefixMap) null))
              .append(" .\n");

        for (Map.Entry<String, RDFNode> entry : output.entrySet()) {
            if ("outcome".equals(entry.getKey())) continue;
            sparql.append("    <").append(invocation.actionIri()).append("> :")
                  .append(entry.getKey()).append(" ")
                  .append(NodeFmtLib.str(entry.getValue().asNode(), (PrefixMap) null))
                  .append(" .\n");
        }

        sparql.append("    << <").append(invocation.actionIri()).append("> :outcome ")
              .append(NodeFmtLib.str(outcomeNode.asNode(), (PrefixMap) null))
              .append(" >> :flow <").append(invocation.flowToken()).append("> .\n");
        sparql.append("  }\n");
        sparql.append("}\n");
        actionLog.update(sparql.toString());
        signalCompletion();
    }
}
