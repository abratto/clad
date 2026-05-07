package com.example.app.concepts.passwordauth;

import com.example.app.engine.FlowManager;
import com.example.app.engine.RdfVocabulary;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * The PasswordAuth concept: holds password verifiers per user id and
 * checks them. Owns its own credential store; never reads
 * {@code UserConcept} state directly (R1).
 */
public final class PasswordAuthConcept {

    public enum AuthOutcome { OK, BAD_PASSWORD, NO_CREDENTIAL }

    private final FlowManager flow;
    private final Map<UUID, String> verifierByUserId = new HashMap<>();

    public PasswordAuthConcept(FlowManager flow) {
        this.flow = flow;
    }

    /** Set or replace the credential for {@code userId}. */
    public void setCredential(UUID userId, String passwordVerifier, UUID parentTokenId, String actor) {
        verifierByUserId.put(userId, passwordVerifier);
        flow.emit(
                "PasswordAuth.setCredential",
                actor,
                parentTokenId,
                Map.of(
                        RdfVocabulary.FIELD_USER_ID, userId,
                        RdfVocabulary.FIELD_OUTCOME, "STORED"));
    }

    /** Check a password against the stored verifier for {@code userId}. */
    public AuthOutcome check(UUID userId, String password, UUID parentTokenId, String actor) {
        String stored = verifierByUserId.get(userId);
        AuthOutcome outcome;
        if (stored == null) {
            outcome = AuthOutcome.NO_CREDENTIAL;
        } else if (stored.equals(password)) {
            outcome = AuthOutcome.OK;
        } else {
            outcome = AuthOutcome.BAD_PASSWORD;
        }
        Map<String, Object> fields = new HashMap<>();
        fields.put(RdfVocabulary.FIELD_USER_ID, userId);
        fields.put(RdfVocabulary.FIELD_OUTCOME, outcome.name());
        flow.emit("PasswordAuth.check", actor, parentTokenId, fields);
        return outcome;
    }
}
