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

    private static final int LOCKOUT_THRESHOLD = 5;
    private static final long LOCKOUT_WINDOW_MILLIS = 15L * 60L * 1000L;
    private static final String CRED_PATH = "cred/";
    private static final String CRED_BINDING = "cred";
    private static final String FAILED_ATTEMPTS_BINDING = "failedAttempts";
    private static final String LOCKED_UNTIL_BINDING = "lockedUntil";
    private static final String USER_ID_BINDING = "userId";
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
        replaceAuthState(userId, verify(password), 0, null);
    }

    private void replaceAuthState(String userId, String verifier, int failedAttempts, Long lockedUntilMillis) {
        deleteAuthState(userId);

        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("p", NS);
        String lockedUntilTriple = lockedUntilMillis == null ? "" : " ; p:lockedUntil ?" + LOCKED_UNTIL_BINDING;
        pss.setCommandText("INSERT DATA { GRAPH ?g { ?cred p:verifier ?verifier ; p:failedAttempts ?failedAttempts"
                + lockedUntilTriple + " . } }");
        pss.setIri("g", GRAPH);
        pss.setIri(CRED_BINDING, NS + CRED_PATH + userId);
        pss.setLiteral("verifier", verifier);
        pss.setLiteral(FAILED_ATTEMPTS_BINDING, failedAttempts);
        if (lockedUntilMillis != null) {
            pss.setLiteral(LOCKED_UNTIL_BINDING, lockedUntilMillis);
        }
        actionLog.update(pss.toString());
    }

    private void deleteAuthState(String userId) {
        var pss = new ParameterizedSparqlString();
        pss.setCommandText("DELETE WHERE { GRAPH ?g { ?cred ?p ?o } }");
        pss.setIri("g", GRAPH);
        pss.setIri(CRED_BINDING, NS + CRED_PATH + userId);
        actionLog.update(pss.toString());
    }

    private void doSet(ActionRecord invocation) {
        String userId = invocation.binding(USER_ID_BINDING);
        String password = invocation.binding("password");
        if (userId == null || password == null) {
            writeError(invocation, "missing userId or password");
            return;
        }
        seedCredential(userId, password);
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral("SET"),
                USER_ID_BINDING, ResourceFactory.createStringLiteral(userId)));
    }

    private void doCheck(ActionRecord invocation) {
        String userId = invocation.binding(USER_ID_BINDING);
        String password = invocation.binding("password");
        if (userId == null || password == null) {
            writeError(invocation, "missing userId or password");
            return;
        }
        String outcome;
        AuthState state = lookupAuthState(userId);
        long now = System.currentTimeMillis();
        if (state == null) {
            outcome = "NO_CREDENTIAL";
        } else if (state.lockedUntilMillis() != null && state.lockedUntilMillis() > now) {
            outcome = "LOCKED";
        } else if (state.verifier().equals(verify(password))) {
            replaceAuthState(userId, state.verifier(), 0, null);
            outcome = "OK";
        } else {
            int failedAttempts = state.failedAttempts() + 1;
            Long lockedUntilMillis = failedAttempts >= LOCKOUT_THRESHOLD
                    ? now + LOCKOUT_WINDOW_MILLIS
                    : null;
            replaceAuthState(userId, state.verifier(), failedAttempts, lockedUntilMillis);
            outcome = "BAD_PASSWORD";
        }
        writeCompletion(invocation, Map.of(
                "outcome", ResourceFactory.createStringLiteral(outcome),
            USER_ID_BINDING, ResourceFactory.createStringLiteral(userId)));
    }

    private AuthState lookupAuthState(String userId) {
        var pss = new ParameterizedSparqlString();
        pss.setNsPrefix("p", NS);
        pss.setCommandText("""
                SELECT ?v ?failedAttempts ?lockedUntil
                WHERE {
                  GRAPH ?g {
                    ?cred p:verifier ?v .
                    OPTIONAL { ?cred p:failedAttempts ?failedAttempts }
                    OPTIONAL { ?cred p:lockedUntil ?lockedUntil }
                  }
                }
                LIMIT 1
                """);
        pss.setIri("g", GRAPH);
        pss.setIri(CRED_BINDING, NS + CRED_PATH + userId);
        List<Map<String, String>> rows = actionLog.select(pss.toString());
        if (rows.isEmpty()) return null;
        Map<String, String> row = rows.get(0);
        return new AuthState(
                row.get("v"),
                row.get(FAILED_ATTEMPTS_BINDING) == null
                    ? 0
                    : Integer.parseInt(row.get(FAILED_ATTEMPTS_BINDING)),
                row.get(LOCKED_UNTIL_BINDING) == null
                    ? null
                    : Long.parseLong(row.get(LOCKED_UNTIL_BINDING)));
    }

    private record AuthState(String verifier, int failedAttempts, Long lockedUntilMillis) {}

    /** Trivial verifier — DO NOT USE IN PRODUCTION. */
    private static String verify(String password) {
        return "sha256:" + Integer.toHexString(password.hashCode());
    }
}
