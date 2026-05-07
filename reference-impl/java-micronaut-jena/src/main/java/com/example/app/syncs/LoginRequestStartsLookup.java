package com.example.app.syncs;

import com.example.app.concepts.user.UserConcept;
import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncAgent;
import com.example.app.engine.SyncTrigger;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Sync: LoginRequestStartsLookup
 *
 * <p>When: {@code Web/request[route=login]}
 * <p>Then: {@code User/lookupByUsername { username }}
 *
 * <p>Bridges the bootstrap concept to the User concept. The {@code username}
 * binding is read straight from the request input.
 *
 * <p>Note: {@code UserConcept.IRI} is referenced as a constant only — no
 * cross-concept Java import of state or behaviour is performed (R1).
 */
@Singleton
public final class LoginRequestStartsLookup extends SyncAgent {

    private static final String WEB_IRI = FlowManager.WEB_CONCEPT_IRI;

    @Inject
    public LoginRequestStartsLookup(ActionLog actionLog) {
        super(actionLog);
    }

    @Override
    public String syncName() { return "loginRequestStartsLookup"; }

    @Override
    public SyncTrigger trigger() { return new SyncTrigger(WEB_IRI, "request", null); }

    @Override
    protected String whereClause() {
        return
            "    ?_when_1 :concept <" + WEB_IRI + "> ;\n" +
            "             :name    \"request\" ;\n" +
            "             :input   ?_web_inp ;\n" +
            "             :flow    ?_flow .\n" +
            "    ?_web_inp :route    \"login\" ;\n" +
            "              :username ?_username .\n";
    }

    @Override
    protected String thenBindings() {
        return
            "    ?_then_1 :concept <" + UserConcept.IRI + "> ;\n" +
            "             :name    \"lookupByUsername\" ;\n" +
            "             :input   ?_then_input .\n" +
            "    ?_then_input :username ?_username .\n";
    }
}
