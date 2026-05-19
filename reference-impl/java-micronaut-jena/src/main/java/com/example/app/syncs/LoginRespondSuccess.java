package com.example.app.syncs;

import com.example.app.concepts.session.SessionConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncMetadata;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: LoginRespondSuccess
 *
 * <p>When: {@code Session/grant[outcome=GRANTED]}
 * <p>Then: {@code Web/respond { statusCode: 200, sessionToken }}
 */
@SyncMetadata(
        flow = "Login",
        step = 4,
        triggeredBy = "Session/grant[GRANTED]",
        fires = "Web/respond[200]")
@Singleton
public final class LoginRespondSuccess extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;

    @Inject
    public LoginRespondSuccess(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "loginRespondSuccess"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(SessionConcept.IRI, "grant", null);
    }

    @Override
    protected String whereClause() {
        return
            "    ?_when_1 :concept <" + SessionConcept.IRI + "> ;\n" +
            "             :name    \"grant\" ;\n" +
            "             :flow    ?_flow ;\n" +
            "             :output  ?_grant_out .\n" +
            "    ?_grant_out :outcome      \"GRANTED\" ;\n" +
            "                :sessionToken ?_sessionToken .\n";
    }

    @Override
    protected String thenBindings() {
        return
            "    ?_then_1 :concept <" + WEB_IRI + "> ;\n" +
            "             :name    \"respond\" ;\n" +
            "             :input   ?_then_input .\n" +
            "    ?_then_input :statusCode   200 ;\n" +
            "                 :sessionToken ?_sessionToken .\n";
    }
}
