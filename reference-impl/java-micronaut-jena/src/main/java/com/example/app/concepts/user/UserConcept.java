package com.example.app.concepts.user;

import com.example.app.engine.ActionLog;
import com.example.app.engine.ActionRecord;
import com.example.app.engine.CompletionBus;
import com.example.app.engine.ConceptAgent;
import com.example.app.engine.RdfVocabulary;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.apache.jena.query.ParameterizedSparqlString;
import org.apache.jena.rdf.model.ResourceFactory;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * The User concept: who exists in the system.
 *
 * <p>State lives in the named graph {@code concept:user}. Two actions:
 * <ul>
 *   <li>{@code register} — adds a (userId, username) record.</li>
 *   <li>{@code lookupByUsername} — emits {@code outcome=FOUND|UNKNOWN}.</li>
 * </ul>
 */
@Singleton
public final class UserConcept extends ConceptAgent {

    /** IRI used in :concept triples. */
    public static final String IRI = "https://clad.dev/concept/user";

    private static final String GRAPH = RdfVocabulary.conceptGraph("user");
    private static final String PROFILE_NS = "https://clad.dev/concept/user#";

    @Inject
    public UserConcept(ActionLog actionLog, CompletionBus completionBus) {
        super(actionLog, completionBus);
    }

    @Override
    protected String conceptIRI() {
        return IRI;
    }

    @Override
    public void pollAll() {
        pollAndProcess("register");
        pollAndProcess("lookupByUsername");
    }

    @Override
    protected void processInvocation(ActionRecord invocation) {
        switch (invocation.actionName()) {
            case "register" -> doRegister(invocation);
            case "lookupByUsername" -> doLookup(invocation);
            default -> writeError(invocation, "unknown action: " + invocation.actionName());
        }
    }

    /** Test/seed helper to pre-populate the user graph. */
    public void seedUser(String userId, String username) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("u", PROFILE_NS);
        pss.setCommandText("INSERT DATA { GRAPH ?g { ?user u:username ?username } }");
        pss.setIri("g", GRAPH);
        pss.setIri("user", PROFILE_NS + "user/" + userId);
        pss.setLiteral("username", username);
        actionLog.update(pss.toString());
    }

    private void doRegister(ActionRecord invocation) {
        String username = invocation.binding("username");
        if (username == null) { writeError(invocation, "missing username"); return; }
        if (existsByUsername(username)) {
            writeRefusal(invocation, "username already taken: " + username);
            return;
        }
        String userId = UUID.randomUUID().toString();
        seedUser(userId, username);
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral("REGISTERED"),
                "userId", ResourceFactory.createStringLiteral(userId),
                "username", ResourceFactory.createStringLiteral(username)));
    }

    private void doLookup(ActionRecord invocation) {
        String username = invocation.binding("username");
        if (username == null) { writeError(invocation, "missing username"); return; }
        String userId = findUserIdByUsername(username);
        if (userId == null) {
            writeRefusal(invocation, "username not found: " + username);
        } else {
            writeCompletion(invocation, Map.of(
                    "outcome", ResourceFactory.createStringLiteral("FOUND"),
                    "userId", ResourceFactory.createStringLiteral(userId),
                    "username", ResourceFactory.createStringLiteral(username)));
        }
    }

    private boolean existsByUsername(String username) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("u", PROFILE_NS);
        pss.setCommandText("ASK { GRAPH ?g { ?user u:username ?username } }");
        pss.setIri("g", GRAPH);
        pss.setLiteral("username", username);
        return actionLog.ask(pss.toString());
    }

    private String findUserIdByUsername(String username) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("u", PROFILE_NS);
        pss.setCommandText("SELECT ?user WHERE { GRAPH ?g { ?user u:username ?username } } LIMIT 1");
        pss.setIri("g", GRAPH);
        pss.setLiteral("username", username);
        List<Map<String, String>> rows = actionLog.select(pss.toString());
        if (rows.isEmpty()) return null;
        String iri = rows.get(0).get("user");
        return iri == null ? null : iri.substring(PROFILE_NS.length() + "user/".length());
    }
}
