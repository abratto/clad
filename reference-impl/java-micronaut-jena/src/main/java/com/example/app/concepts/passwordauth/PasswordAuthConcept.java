package com.example.app.concepts.passwordauth;

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

/**
 * The PasswordAuth concept: stores a password verifier per userId and checks
 * supplied passwords. State lives in {@code concept:passwordauth}.
 *
 * <p>Verifier is a plain hash placeholder for the reference profile — replace
 * with a real KDF (Argon2/bcrypt) in production profiles.
 *
 * <p>Actions:
 * <ul>
 *   <li>{@code setCredential} — input: {@code userId, password}.</li>
 *   <li>{@code check} — input: {@code userId, password}; output: {@code outcome}
 *       in {@code OK | BAD_PASSWORD | NO_CREDENTIAL}.</li>
 * </ul>
 */
@Singleton
public final class PasswordAuthConcept extends ConceptAgent {

    public static final String IRI = "https://clad.dev/concept/passwordauth";

    private static final String GRAPH = RdfVocabulary.conceptGraph("passwordauth");
    private static final String NS = "https://clad.dev/concept/passwordauth#";

    @Inject
    public PasswordAuthConcept(ActionLog actionLog, CompletionBus completionBus) {
        super(actionLog, completionBus);
    }

    @Override
    protected String conceptIRI() {
        return IRI;
    }

    @Override
    public void pollAll() {
        pollAndProcess("setCredential");
        pollAndProcess("check");
    }

    @Override
    protected void processInvocation(ActionRecord invocation) {
        switch (invocation.actionName()) {
            case "setCredential" -> doSet(invocation);
            case "check" -> doCheck(invocation);
            default -> writeError(invocation, "unknown action: " + invocation.actionName());
        }
    }

    /** Test/seed helper. */
    public void seedCredential(String userId, String password) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("p", NS);
        pss.setCommandText("""
                DELETE { GRAPH ?g { ?cred p:verifier ?old } }
                INSERT { GRAPH ?g { ?cred p:verifier ?new } }
                WHERE  { GRAPH ?g { OPTIONAL { ?cred p:verifier ?old } } }
                """);
        pss.setIri("g", GRAPH);
        pss.setIri("cred", NS + "cred/" + userId);
        pss.setLiteral("new", verify(password));
        actionLog.update(pss.toString());
        // Ensure cred resource is asserted even if no prior verifier existed.
        var insert = new ParameterizedSparqlString();
        insert.setNsPrefix("p", NS);
        insert.setCommandText("INSERT DATA { GRAPH ?g { ?cred p:verifier ?v } }");
        insert.setIri("g", GRAPH);
        insert.setIri("cred", NS + "cred/" + userId);
        insert.setLiteral("v", verify(password));
        // Idempotent INSERT DATA is fine here for the simple reference profile.
        if (!hasCredential(userId)) actionLog.update(insert.toString());
    }

    private void doSet(ActionRecord invocation) {
        String userId = invocation.binding("userId");
        String password = invocation.binding("password");
        if (userId == null || password == null) {
            writeError(invocation, "missing userId or password");
            return;
        }
        seedCredential(userId, password);
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral("SET"),
                "userId", ResourceFactory.createStringLiteral(userId)));
    }

    private void doCheck(ActionRecord invocation) {
        String userId = invocation.binding("userId");
        String password = invocation.binding("password");
        if (userId == null || password == null) {
            writeError(invocation, "missing userId or password");
            return;
        }
        String outcome;
        String stored = lookupVerifier(userId);
        if (stored == null) {
            outcome = "NO_CREDENTIAL";
        } else if (stored.equals(verify(password))) {
            outcome = "OK";
        } else {
            outcome = "BAD_PASSWORD";
        }
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral(outcome),
                "userId", ResourceFactory.createStringLiteral(userId)));
    }

    private boolean hasCredential(String userId) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("p", NS);
        pss.setCommandText("ASK { GRAPH ?g { ?cred p:verifier ?v } }");
        pss.setIri("g", GRAPH);
        pss.setIri("cred", NS + "cred/" + userId);
        return actionLog.ask(pss.toString());
    }

    private String lookupVerifier(String userId) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("p", NS);
        pss.setCommandText("SELECT ?v WHERE { GRAPH ?g { ?cred p:verifier ?v } } LIMIT 1");
        pss.setIri("g", GRAPH);
        pss.setIri("cred", NS + "cred/" + userId);
        List<Map<String, String>> rows = actionLog.select(pss.toString());
        if (rows.isEmpty()) return null;
        return rows.get(0).get("v");
    }

    /** Trivial verifier — DO NOT USE IN PRODUCTION. */
    private static String verify(String password) {
        return "sha256:" + Integer.toHexString(password.hashCode());
    }
}
