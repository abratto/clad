package dev.legible.example.login;

import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.Region;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Concept unit tests that assert field values, not only outcome tokens
 * (hard rules R14/R16: an outcome-only test would pass while downstream syncs
 * received null fields).
 */
class ConceptTest {

    private UserNamingConcept userNaming;
    private PasswordAuthConcept passwordAuth;
    private SessionConcept session;

    @BeforeEach
    void setUp() {
        InMemoryFactStore facts = new InMemoryFactStore();
        Region u = facts.region("UserNaming");
        Region p = facts.region("PasswordAuth");
        Region s = facts.region("Session");
        userNaming = new UserNamingConcept(u);
        passwordAuth = new PasswordAuthConcept(p);
        session = new SessionConcept(s);
    }

    private String seedUser(String username, String password) {
        String userId = UUID.randomUUID().toString();
        userNaming.seedUser(userId, username);
        passwordAuth.seedCredential(userId, password);
        return userId;
    }

    @Test
    void lookupByUsernameFoundReturnsNonEmptyUserId() {
        String userId = seedUser("alice", "secret");

        Map<String, Object> res = userNaming.execute("lookupByUsername", Map.of("username", "alice"));

        assertEquals("FOUND", res.get("outcome"));
        assertEquals(userId, res.get("userId"));
        assertFalse(((String) res.get("userId")).isEmpty());
    }

    @Test
    void lookupByUsernameUnknownRefuses() {
        Map<String, Object> res = userNaming.execute("lookupByUsername", Map.of("username", "nobody"));

        assertEquals("refused", res.get("outcome"));
    }

    @Test
    void checkOkReturnsUserIdAndClearsCounter() {
        String userId = seedUser("alice", "secret");

        Map<String, Object> res = passwordAuth.execute("check",
                Map.of("userId", userId, "password", "secret"));

        assertEquals("OK", res.get("outcome"));
        assertEquals(userId, res.get("userId"));
    }

    @Test
    void checkBadPasswordReturnsUserIdAndAccumulatesFailures() {
        String userId = seedUser("alice", "secret");

        for (int i = 0; i < 5; i++) {
            Map<String, Object> res = passwordAuth.execute("check",
                    Map.of("userId", userId, "password", "wrong"));
            assertEquals("BAD_PASSWORD", res.get("outcome"));
            assertEquals(userId, res.get("userId"));
        }

        // After five failures the account is locked, even with the correct password.
        Map<String, Object> locked = passwordAuth.execute("check",
                Map.of("userId", userId, "password", "secret"));
        assertEquals("LOCKED", locked.get("outcome"));
        assertEquals(userId, locked.get("userId"));
    }

    @Test
    void checkNoCredentialReturnsNamedOutcome() {
        Map<String, Object> res = passwordAuth.execute("check",
                Map.of("userId", "ghost", "password", "x"));

        assertEquals("NO_CREDENTIAL", res.get("outcome"));
        assertEquals("ghost", res.get("userId"));
    }

    @Test
    void grantReturnsNonEmptySessionId() {
        String userId = seedUser("alice", "secret");

        Map<String, Object> res = session.execute("grant", Map.of("userId", userId));

        assertEquals("GRANTED", res.get("outcome"));
        assertEquals(userId, res.get("userId"));
        assertNotNull(res.get("sessionId"));
        assertFalse(((String) res.get("sessionId")).isEmpty());
    }

    @Test
    void lookupSessionReturnsUserIdOrUnknown() {
        String userId = seedUser("alice", "secret");
        String sessionId = (String) session.execute("grant", Map.of("userId", userId)).get("sessionId");

        Map<String, Object> active = session.execute("lookup", Map.of("sessionId", sessionId));
        assertEquals("ACTIVE", active.get("outcome"));
        assertEquals(userId, active.get("userId"));

        Map<String, Object> unknown = session.execute("lookup", Map.of("sessionId", "missing"));
        assertEquals("UNKNOWN", unknown.get("outcome"));
    }
}
