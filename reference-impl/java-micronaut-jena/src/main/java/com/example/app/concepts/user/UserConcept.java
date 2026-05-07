package com.example.app.concepts.user;

import com.example.app.engine.FlowManager;
import com.example.app.engine.FlowToken;
import com.example.app.engine.RdfVocabulary;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * The User concept: who exists in the system.
 *
 * <p>Honours R1 (no cross-concept imports), R2 (owns its own state
 * region — here, an in-memory map), R5 (every public action emits a
 * flow token).
 */
public final class UserConcept {

    public enum RegisterOutcome { REGISTERED, USERNAME_TAKEN }

    private final FlowManager flow;
    private final Map<UUID, String> usernamesById = new HashMap<>();
    private final Map<String, UUID> idsByUsername = new HashMap<>();

    public UserConcept(FlowManager flow) {
        this.flow = flow;
    }

    /** Register a new user. */
    public RegisterOutcome register(String username, UUID parentTokenId, String actor) {
        if (idsByUsername.containsKey(username)) {
            flow.emit(
                    "User.register",
                    actor,
                    parentTokenId,
                    Map.of(
                            RdfVocabulary.FIELD_USERNAME, username,
                            RdfVocabulary.FIELD_OUTCOME, RegisterOutcome.USERNAME_TAKEN.name()));
            return RegisterOutcome.USERNAME_TAKEN;
        }
        UUID id = UUID.randomUUID();
        usernamesById.put(id, username);
        idsByUsername.put(username, id);
        flow.emit(
                "User.register",
                actor,
                parentTokenId,
                Map.of(
                        RdfVocabulary.FIELD_USER_ID, id,
                        RdfVocabulary.FIELD_USERNAME, username,
                        RdfVocabulary.FIELD_OUTCOME, RegisterOutcome.REGISTERED.name()));
        return RegisterOutcome.REGISTERED;
    }

    /** Look up a user id by username, emitting a lookup token. */
    public Optional<UUID> lookupByUsername(String username, UUID parentTokenId, String actor) {
        UUID id = idsByUsername.get(username);
        Map<String, Object> fields = new HashMap<>();
        fields.put(RdfVocabulary.FIELD_USERNAME, username);
        fields.put(RdfVocabulary.FIELD_OUTCOME, id == null ? "UNKNOWN" : "FOUND");
        if (id != null) {
            fields.put(RdfVocabulary.FIELD_USER_ID, id);
        }
        FlowToken t = flow.emit("User.lookupByUsername", actor, parentTokenId, fields);
        // referenced to keep the variable in use; tests can read the log.
        assert t != null;
        return Optional.ofNullable(id);
    }
}
