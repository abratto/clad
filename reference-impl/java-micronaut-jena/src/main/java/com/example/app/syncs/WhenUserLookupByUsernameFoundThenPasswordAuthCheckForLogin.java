package com.example.app.syncs;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.user.UserConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncMetadata;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin
 *
 * <p>When: {@code User/lookupByUsername[outcome=FOUND]} (in a login flow)
 * <p>Then: {@code PasswordAuth/check { userId, password }}
 *
 * <p>Joins the User lookup output (for {@code userId}) with the original Web
 * request input (for {@code password}) via shared {@code ?_flow}.
 */
@SyncMetadata(
        flow = "Login",
        step = 2,
        triggeredBy = "User/lookupByUsername[FOUND]",
        fires = "PasswordAuth/check",
        where = "same flow as the login request")
@Singleton
public final class WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;
    private static final String LOGIN_ROUTE = "login";

    @Inject
    public WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "whenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(UserConcept.IRI, "lookupByUsername", null);
    }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "lookupByUsername" ;
                     :userId  ?_userId .
            << ?_when_1 :outcome "FOUND" >> :flow ?_flow .
            ?_web_req :concept <%s> ;
                      :name    "request" ;
                      :flow    ?_flow ;
                      :input   ?_web_inp .
            ?_web_inp :route    ?_route ;
                      :password ?_password .
            """.formatted(UserConcept.IRI, WEB_IRI);
    }

    @Override
    protected String thenBindings() {
        return """
            ?_then_1 :concept <%s> ;
                     :name    "check" ;
                     :input   [ :userId ?_userId ; :password ?_password ] .
            """.formatted(PasswordAuthConcept.IRI);
    }

    @Override
    protected String parameterizeSparql(String sparql) {
        return bindLiteral(sparql, "_route", LOGIN_ROUTE);
    }
}
