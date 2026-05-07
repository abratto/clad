package com.example.app.syncs;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.session.SessionConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: LoginGrantsSession
 *
 * <p>Spec: {@code features/UC-00-login/stages/03_syncs/output/LoginGrantsSession.sync.md}
 *
 * <p>When: {@code PasswordAuth/check[outcome=OK]}
 * <p>Then: {@code Session/grant { userId }}
 */
@Singleton
public final class LoginGrantsSession extends SyncAgent {

    @Inject
    public LoginGrantsSession(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "loginGrantsSession"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(PasswordAuthConcept.IRI, "check", null);
    }

    @Override
    protected String whereClause() {
        return
            "    ?_when_1 :concept <" + PasswordAuthConcept.IRI + "> ;\n" +
            "             :name    \"check\" ;\n" +
            "             :flow    ?_flow ;\n" +
            "             :output  ?_check_out .\n" +
            "    ?_check_out :outcome \"OK\" ;\n" +
            "                :userId  ?_userId .\n";
    }

    @Override
    protected String thenBindings() {
        return
            "    ?_then_1 :concept <" + SessionConcept.IRI + "> ;\n" +
            "             :name    \"grant\" ;\n" +
            "             :input   ?_then_input .\n" +
            "    ?_then_input :userId ?_userId .\n";
    }
}
