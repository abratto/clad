package com.example.app.syncs;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: LoginRespondWrongPassword
 *
 * <p>When: {@code PasswordAuth/check[outcome=BAD_PASSWORD]}
 * <p>Then: {@code Web/respond { statusCode: 401, message }}
 *
 * <p>The message is intentionally identical to the unknown-user response so
 * the API does not leak account enumeration.
 */
@Singleton
public final class LoginRespondWrongPassword extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;
    static final String LOGIN_FAILURE_MESSAGE = "username or password didn't match";

    @Inject
    public LoginRespondWrongPassword(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "loginRespondWrongPassword"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(PasswordAuthConcept.IRI, "check", null);
    }

    @Override
    protected String whereClause() {
        // Match BAD_PASSWORD or NO_CREDENTIAL — both are credential failures and
        // must be indistinguishable from unknown-user externally.
        return
            "    ?_when_1 :concept <" + PasswordAuthConcept.IRI + "> ;\n" +
            "             :name    \"check\" ;\n" +
            "             :flow    ?_flow ;\n" +
            "             :output  ?_check_out .\n" +
            "    ?_check_out :outcome ?_outcome .\n" +
            "    FILTER (?_outcome IN (\"BAD_PASSWORD\", \"NO_CREDENTIAL\"))\n";
    }

    @Override
    protected String thenBindings() {
        return
            "    ?_then_1 :concept <" + WEB_IRI + "> ;\n" +
            "             :name    \"respond\" ;\n" +
            "             :input   ?_then_input .\n" +
            "    ?_then_input :statusCode 401 ;\n" +
            "                 :message    \"" + LOGIN_FAILURE_MESSAGE + "\" .\n";
    }
}
