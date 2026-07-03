package com.example.app.syncs;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.session.SessionConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncMetadata;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: WhenPasswordAuthCheckOkThenSessionGrantForLogin
 *
 * <p>Spec: {@code features/UC-00-login/stages/03_syncs/output/WhenPasswordAuthCheckOkThenSessionGrantForLogin.sync.md}
 *
 * <p>When: {@code PasswordAuth/check[outcome=OK]}
 * <p>Then: {@code Session/grant { userId }}
 */
@SyncMetadata(
        flow = "Login",
        step = 3,
        triggeredBy = "PasswordAuth/check[OK]",
        fires = "Session/grant")
@Singleton
public final class WhenPasswordAuthCheckOkThenSessionGrantForLogin extends SyncAgent {

    @Inject
    public WhenPasswordAuthCheckOkThenSessionGrantForLogin(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "whenPasswordAuthCheckOkThenSessionGrantForLogin"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(PasswordAuthConcept.IRI, "check", null);
    }

    @Override
    protected String whereClause() {
        return """
            ?_when_1 :concept <%s> ;
                     :name    "check" ;
                     :userId  ?_userId .
            << ?_when_1 :outcome "OK" >> :flow ?_flow .
            """.formatted(PasswordAuthConcept.IRI);
    }

    @Override
    protected String thenBindings() {
        return """
            ?_then_1 :concept <%s> ;
                     :name    "grant" ;
                     :input   [ :userId ?_userId ] .
            """.formatted(SessionConcept.IRI);
    }
}
