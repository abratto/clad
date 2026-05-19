package com.example.app.syncs;

import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.user.UserConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncMetadata;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: LoginLookupTriggersAuth
 *
 * <p>When: {@code User/lookupByUsername[outcome=FOUND]} (in a login flow)
 * <p>Then: {@code PasswordAuth/check { userId, password }}
 *
 * <p>Joins the User lookup output (for {@code userId}) with the original Web
 * request input (for {@code password}) via shared {@code ?_flow}.
 */
@SyncMetadata(
        flow = "Login",
        step = 2,
        triggeredBy = "User/lookupByUsername[FOUND]",
        fires = "PasswordAuth/check",
        where = "same flow as the login request")
@Singleton
public final class LoginLookupTriggersAuth extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;

    @Inject
    public LoginLookupTriggersAuth(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "loginLookupTriggersAuth"; }

    @Override
    public SyncTrigger trigger() {
        return new SyncTrigger(UserConcept.IRI, "lookupByUsername", null);
    }

    @Override
    protected String whereClause() {
        return
            "    ?_when_1 :concept <" + UserConcept.IRI + "> ;\n" +
            "             :name    \"lookupByUsername\" ;\n" +
            "             :flow    ?_flow ;\n" +
            "             :output  ?_lookup_out .\n" +
            "    ?_lookup_out :outcome \"FOUND\" ;\n" +
            "                 :userId  ?_userId .\n" +
            "    ?_web_req :concept <" + WEB_IRI + "> ;\n" +
            "              :name    \"request\" ;\n" +
            "              :flow    ?_flow ;\n" +
            "              :input   ?_web_inp .\n" +
            "    ?_web_inp :route    \"login\" ;\n" +
            "              :password ?_password .\n";
    }

    @Override
    protected String thenBindings() {
        return
            "    ?_then_1 :concept <" + PasswordAuthConcept.IRI + "> ;\n" +
            "             :name    \"check\" ;\n" +
            "             :input   ?_then_input .\n" +
            "    ?_then_input :userId   ?_userId ;\n" +
            "                 :password ?_password .\n";
    }
}
