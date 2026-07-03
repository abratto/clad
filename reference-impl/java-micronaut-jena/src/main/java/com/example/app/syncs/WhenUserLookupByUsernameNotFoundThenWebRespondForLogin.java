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
 * Sync: WhenUserLookupByUsernameNotFoundThenWebRespondForLogin
 *
 * <p>When: {@code User/lookupByUsername[outcome=UNKNOWN]}
 * <p>Then: {@code Web/respond { statusCode: 401, message }}
 *
 * <p>Same message as {@link WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin} — no enumeration leak.
 */
@SyncMetadata(
        flow = "Login",
        step = 2,
        triggeredBy = "User/lookupByUsername[UNKNOWN]",
        fires = "Web/respond[401]",
        where = "unknown-user path")
@Singleton
public final class WhenUserLookupByUsernameNotFoundThenWebRespondForLogin extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;

    @Inject
    public WhenUserLookupByUsernameNotFoundThenWebRespondForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "whenUserLookupByUsernameNotFoundThenWebRespondForLogin"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(UserConcept.IRI, "lookupByUsername", null);
    }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "lookupByUsername" .
            << ?_when_1 :outcome "UNKNOWN" >> :flow ?_flow .
            """.formatted(UserConcept.IRI);
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
        return bindLiteral(sparql, "_message", WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.LOGIN_FAILURE_MESSAGE);
    }
}
