package com.example.app.concepts.session;

import com.example.app.engine.FlowManager;
import com.example.app.engine.RdfVocabulary;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * The Session concept: mints and looks up session tokens. Owns its own
 * session map; never reads {@code UserConcept} or
 * {@code PasswordAuthConcept} state directly (R1).
 */
public final class SessionConcept {

    public enum GrantOutcome { GRANTED }
    public enum LookupOutcome { ACTIVE, UNKNOWN }

    private final FlowManager flow;
    private final Map<UUID, UUID> userIdBySession = new HashMap<>();

    public SessionConcept(FlowManager flow) {
        this.flow = flow;
    }

    /** Mint a new session for {@code userId} and return the session id. */
    public UUID grant(UUID userId, UUID parentTokenId, String actor) {
        UUID sessionId = UUID.randomUUID();
        userIdBySession.put(sessionId, userId);
        flow.emit(
                "Session.grant",
                actor,
                parentTokenId,
                Map.of(
                        RdfVocabulary.FIELD_USER_ID, userId,
                        RdfVocabulary.FIELD_SESSION_ID, sessionId,
                        RdfVocabulary.FIELD_OUTCOME, GrantOutcome.GRANTED.name()));
        return sessionId;
    }

    /** Look up the user id behind a session token. */
    public Optional<UUID> lookup(UUID sessionId, UUID parentTokenId, String actor) {
        UUID userId = userIdBySession.get(sessionId);
        Map<String, Object> fields = new HashMap<>();
        fields.put(RdfVocabulary.FIELD_SESSION_ID, sessionId);
        fields.put(
                RdfVocabulary.FIELD_OUTCOME,
                userId == null ? LookupOutcome.UNKNOWN.name() : LookupOutcome.ACTIVE.name());
        if (userId != null) {
            fields.put(RdfVocabulary.FIELD_USER_ID, userId);
        }
        flow.emit("Session.lookup", actor, parentTokenId, fields);
        return Optional.ofNullable(userId);
    }
}
