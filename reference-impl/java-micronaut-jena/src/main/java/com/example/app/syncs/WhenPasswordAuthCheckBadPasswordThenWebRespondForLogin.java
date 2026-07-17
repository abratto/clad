package com.example.app.syncs;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncMetadata;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin
 *
 * <p>When: {@code PasswordAuth/check[outcome=BAD_PASSWORD]}
 * <p>Then: {@code Web/respond { statusCode: 401, message }}
 *
 * <p>The message is intentionally identical to the unknown-user response so
 * the API does not leak account enumeration.
 */
@SyncMetadata(
        flow = "Login",
        step = 3,
        triggeredBy = "PasswordAuth/check[BAD_PASSWORD|NO_CREDENTIAL]",
        fires = "Web/respond[401]",
        where = "credential failure path")
@Singleton
public final class WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;
    private static final String LOGIN_ROUTE = "login";
    static final String LOGIN_FAILURE_MESSAGE = "username or password didn't match";

    @Inject
    public WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "whenPasswordAuthCheckBadPasswordThenWebRespondForLogin"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(PasswordAuthConcept.IRI, "check", null);
    }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "check" .
            << ?_when_1 :outcome ?_outcome >> :flow ?_flow .
            FILTER (?_outcome IN ("BAD_PASSWORD", "NO_CREDENTIAL"))
            ?_web_req :concept <%s> ;
                      :name    "request" ;
                      :flow    ?_flow ;
                      :input   ?_web_inp .
            ?_web_inp :route ?_route .
            """.formatted(PasswordAuthConcept.IRI, WEB_IRI);
    }

    @Override
    protected String thenBindings() {
        return """
            ?_then_1 :concept <%s> ;
                     :name    "respond" ;
                     :input   [ :statusCode 401 ; :message ?_message ] .
            """.formatted(WEB_IRI);
    }

    @Override
    protected String parameterizeSparql(String sparql) {
        sparql = bindLiteral(sparql, "_route", LOGIN_ROUTE);
        return bindLiteral(sparql, "_message", LOGIN_FAILURE_MESSAGE);
    }
}
