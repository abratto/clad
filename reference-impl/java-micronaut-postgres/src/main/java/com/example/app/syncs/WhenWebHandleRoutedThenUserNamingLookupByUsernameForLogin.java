package com.example.app.syncs;

import com.example.app.concepts.usernaming.UserNamingConcept;
import dev.clad.engine.ActionLog;
import dev.clad.engine.FlowManager;
import dev.clad.engine.SyncAgent;
import dev.clad.engine.SyncMetadata;
import dev.clad.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: WhenWebHandleRoutedThenUserNamingLookupByUsernameForLogin
 *
 * <p>When: {@code Web/request[route=login]}
 * <p>Then: {@code UserNaming/lookupByUsername { username }}
 *
 * <p>Bridges the bootstrap concept to the User concept. The {@code username}
 * binding is read straight from the request input.
 *
 * <p>Note: {@code UserNamingConcept.IRI} is referenced as a constant only — no
 * cross-concept Java import of state or behaviour is performed (R1).
 */
@SyncMetadata(
        flow = "Login",
        step = 1,
        triggeredBy = "Web/request[route=login]",
        fires = "UserNaming/lookupByUsername",
        where = "route=login")
@Singleton
public final class WhenWebHandleRoutedThenUserNamingLookupByUsernameForLogin extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;
    private static final String LOGIN_ROUTE = "login";

    @Inject
    public WhenWebHandleRoutedThenUserNamingLookupByUsernameForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "whenWebHandleRoutedThenUserNamingLookupByUsernameForLogin"; }

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
            """.formatted(UserNamingConcept.IRI);
    }

    @Override
    protected String parameterizeSparql(String sparql) {
        return bindLiteral(sparql, "_route", LOGIN_ROUTE);
    }
}
