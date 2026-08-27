package com.example.app.concepts.session;

import dev.clad.engine.ActionLog;
import dev.clad.engine.ActionRecord;
import dev.clad.engine.CompletionBus;
import dev.clad.engine.ConceptAgent;
import dev.clad.engine.SyncEvaluator;
import dev.clad.engine.RdfVocabulary;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.apache.jena.query.ParameterizedSparqlString;
import org.apache.jena.rdf.model.ResourceFactory;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * The Session concept: mints opaque session tokens for authenticated users.
 * State lives in {@code concept:session}.
 *
 * <p>Actions:
 * <ul>
 *   <li>{@code grant} — input: {@code userId}; output:
 *       {@code outcome=GRANTED, sessionId=<uuid>}.</li>
 *   <li>{@code lookup} — input: {@code sessionId}; output:
 *       {@code outcome=ACTIVE|UNKNOWN, userId=...}.</li>
 * </ul>
 */
@Singleton
public final class SessionConcept extends ConceptAgent {

    public static final String IRI = "https://clad.dev/concept/session";

    private static final String GRAPH = RdfVocabulary.conceptGraph("session");
    private static final String NS = "https://clad.dev/concept/session#";

    @Inject
    public SessionConcept(ActionLog actionLog, CompletionBus completionBus,
                          SyncEvaluator evaluator) {
        super(actionLog, completionBus, evaluator);
    }

    /** Test-only constructor. */
    public SessionConcept(ActionLog actionLog, CompletionBus completionBus) {
        super(actionLog, completionBus);
    }

    @Override
    protected String conceptIRI() {
        return IRI;
    }

    @Override
    public void pollAll() {
        pollAndProcess("grant");
        pollAndProcess("lookup");
    }

    @Override
    protected void processInvocation(ActionRecord invocation) {
        switch (invocation.actionName()) {
            case "grant" -> doGrant(invocation);
            case "lookup" -> doLookup(invocation);
            default -> writeError(invocation, "unknown action: " + invocation.actionName());
        }
    }

    private void doGrant(ActionRecord invocation) {
        String userId = invocation.binding("userId");
        if (userId == null) {
            writeError(invocation, "missing userId");
            return;
        }
        String sessionId = UUID.randomUUID().toString();
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("s", NS);
        pss.setCommandText("INSERT DATA { GRAPH ?g { ?session s:userId ?userId } }");
        pss.setIri("g", GRAPH);
        pss.setIri("session", NS + "session/" + sessionId);
        pss.setLiteral("userId", userId);
        actionLog.update(pss.toString());

        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral("GRANTED"),
                "sessionId", ResourceFactory.createStringLiteral(sessionId),
                "userId", ResourceFactory.createStringLiteral(userId)));
    }

    private void doLookup(ActionRecord invocation) {
        String sessionId = invocation.binding("sessionId");
        if (sessionId == null) {
            writeError(invocation, "missing sessionId");
            return;
        }
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("s", NS);
        pss.setCommandText("SELECT ?userId WHERE { GRAPH ?g { ?session s:userId ?userId } } LIMIT 1");
        pss.setIri("g", GRAPH);
        pss.setIri("session", NS + "session/" + sessionId);
        List<Map<String, String>> rows = actionLog.select(pss.toString());
        if (rows.isEmpty()) {
            writeCompletion(invocation, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("UNKNOWN"),
                    "sessionId", ResourceFactory.createStringLiteral(sessionId)));
        } else {
            writeCompletion(invocation, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("ACTIVE"),
                    "sessionId", ResourceFactory.createStringLiteral(sessionId),
                    "userId", ResourceFactory.createStringLiteral(rows.get(0).get("userId"))));
        }
    }
}
