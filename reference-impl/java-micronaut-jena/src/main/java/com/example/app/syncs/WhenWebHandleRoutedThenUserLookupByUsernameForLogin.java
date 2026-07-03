package com.example.app.syncs;

import com.example.app.concepts.user.UserConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncMetadata;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: WhenWebHandleRoutedThenUserLookupByUsernameForLogin
 *
 * <p>When: {@code Web/request[route=login]}
 * <p>Then: {@code User/lookupByUsername { username }}
 *
 * <p>Bridges the bootstrap concept to the User concept. The {@code username}
 * binding is read straight from the request input.
 *
 * <p>Note: {@code UserConcept.IRI} is referenced as a constant only — no
 * cross-concept Java import of state or behaviour is performed (R1).
 */
@SyncMetadata(
        flow = "Login",
        step = 1,
        triggeredBy = "Web/request[route=login]",
        fires = "User/lookupByUsername",
        where = "route=login")
@Singleton
public final class WhenWebHandleRoutedThenUserLookupByUsernameForLogin extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;
    private static final String LOGIN_ROUTE = "login";

    @Inject
    public WhenWebHandleRoutedThenUserLookupByUsernameForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "whenWebHandleRoutedThenUserLookupByUsernameForLogin"; }

    @Override
    public SyncTrigger trigger() { return new SyncTrigger(WEB_IRI, "request", null); }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "request" ;
                     :input   ?_web_inp ;
                     :flow    ?_flow .
            ?_web_inp :route    ?_route ;
                      :username ?_username .
            """.formatted(WEB_IRI);
    }

    @Override
    protected String thenBindings() {
        return """
            ?_then_1 :concept <%s> ;
                     :name    "lookupByUsername" ;
                     :input   [ :username ?_username ] .
            """.formatted(UserConcept.IRI);
    }

    @Override
    protected String parameterizeSparql(String sparql) {
        return bindLiteral(sparql, "_route", LOGIN_ROUTE);
    }
}
