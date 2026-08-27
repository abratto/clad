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
 * Sync: WhenUserNamingLookupByUsernameRefusedThenWebRespondForLogin
 *
 * <p>When: {@code UserNaming/lookupByUsername[refused]}
 * <p>Then: {@code Web/respond { statusCode: 401, message }}
 *
 * <p>Matches the {@code :outcome "refused"} RDF-star annotation. Same message
 * as {@link WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin} — no
 * enumeration leak.
 */
@SyncMetadata(
        flow = "Login",
        step = 2,
        triggeredBy = "UserNaming/lookupByUsername[refused]",
        fires = "Web/respond[401]",
        where = "unknown-user path")
@Singleton
public final class WhenUserNamingLookupByUsernameRefusedThenWebRespondForLogin extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;
    private static final String LOGIN_ROUTE = "login";

    @Inject
    public WhenUserNamingLookupByUsernameRefusedThenWebRespondForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() {         return "whenUserNamingLookupByUsernameRefusedThenWebRespondForLogin"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(UserNamingConcept.IRI, "lookupByUsername", null);
    }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "lookupByUsername" .
            << ?_when_1 :outcome "refused" >> :flow ?_flow .
            ?_web_req :concept <%s> ;
                      :name    "request" ;
                      :flow    ?_flow ;
                      :input   ?_web_inp .
            ?_web_inp :route ?_route .
            """.formatted(UserNamingConcept.IRI, WEB_IRI);
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
        return bindLiteral(sparql, "_message", WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.LOGIN_FAILURE_MESSAGE);
    }
}
