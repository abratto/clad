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
 * Sync: LoginRespondUnknownUser
 *
 * <p>When: {@code User/lookupByUsername[outcome=UNKNOWN]}
 * <p>Then: {@code Web/respond { statusCode: 401, message }}
 *
 * <p>Same message as {@link LoginRespondWrongPassword} — no enumeration leak.
 */
@SyncMetadata(
        flow = "Login",
        step = 2,
        triggeredBy = "User/lookupByUsername[UNKNOWN]",
        fires = "Web/respond[401]",
        where = "unknown-user path")
@Singleton
public final class LoginRespondUnknownUser extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;

    @Inject
    public LoginRespondUnknownUser(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "loginRespondUnknownUser"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(UserConcept.IRI, "lookupByUsername", null);
    }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "lookupByUsername" ;
                     :flow    ?_flow ;
                     :output  ?_lookup_out .
            ?_lookup_out :outcome "UNKNOWN" .
            """.formatted(UserConcept.IRI);
    }

    @Override
    protected String thenBindings() {
        return """
            ?_then_1 :concept <%s> ;
                     :name    "respond" ;
                     :input   ?_then_input .
            ?_then_input :statusCode 401 ;
                         :message    ?_message .
            """.formatted(WEB_IRI);
    }

    @Override
    protected String parameterizeSparql(String sparql) {
        return bindLiteral(sparql, "_message", LoginRespondWrongPassword.LOGIN_FAILURE_MESSAGE);
    }
}
