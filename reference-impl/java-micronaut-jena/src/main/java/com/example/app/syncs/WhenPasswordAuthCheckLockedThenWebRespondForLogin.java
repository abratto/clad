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
 * Sync: WhenPasswordAuthCheckLockedThenWebRespondForLogin
 *
 * <p>When: {@code PasswordAuth/check[outcome=LOCKED]}
 * <p>Then: {@code Web/respond { statusCode: 401, message }}
 */
@SyncMetadata(
        flow = "Login",
        step = 3,
        triggeredBy = "PasswordAuth/check[LOCKED]",
        fires = "Web/respond[401]",
        where = "locked account path")
@Singleton
public final class WhenPasswordAuthCheckLockedThenWebRespondForLogin extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;
    private static final String LOGIN_ROUTE = "login";
    private static final String LOCKED_MESSAGE = "Too many attempts. Try again in 15 minutes.";

    @Inject
    public WhenPasswordAuthCheckLockedThenWebRespondForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "whenPasswordAuthCheckLockedThenWebRespondForLogin"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(PasswordAuthConcept.IRI, "check", null);
    }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "check" .
            << ?_when_1 :outcome "LOCKED" >> :flow ?_flow .
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
        return bindLiteral(sparql, "_message", LOCKED_MESSAGE);
    }
}