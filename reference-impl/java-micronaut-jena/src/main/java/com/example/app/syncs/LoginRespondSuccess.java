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
        return """
            ?_when_1 :concept <%s> ;
                     :name    "grant" ;
                     :sessionToken ?_sessionToken .
            << ?_when_1 :outcome "GRANTED" >> :flow ?_flow .
            """.formatted(SessionConcept.IRI);
    }

    @Override
    protected String thenBindings() {
        return """
            ?_then_1 :concept <%s> ;
                     :name    "respond" ;
                     :input   [ :statusCode 200 ; :sessionToken ?_sessionToken ] .
            """.formatted(WEB_IRI);
    }
}
