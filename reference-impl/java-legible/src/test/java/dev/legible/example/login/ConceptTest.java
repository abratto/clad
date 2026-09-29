package dev.legible.example.login;

import dev.legible.engine.InMemoryFactStore;
import dev.legible.engine.Region;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
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

    @Test
    void registerFreshUsernameReturnsRegisteredWithFields() {
        Map<String, Object> res = userNaming.execute("register", Map.of("username", "bob"));

        assertEquals("REGISTERED", res.get("outcome"));
        assertEquals("bob", res.get("username"));
        assertNotNull(res.get("userId"));
        assertFalse(((String) res.get("userId")).isEmpty());

        // The registration is observable through lookup (the write happened).
        Map<String, Object> found = userNaming.execute("lookupByUsername",
                Map.of("username", "bob"));
        assertEquals("FOUND", found.get("outcome"));
        assertEquals(res.get("userId"), found.get("userId"));
    }

    @Test
    void registerDuplicateUsernameIsRefused() {
        userNaming.execute("register", Map.of("username", "bob"));

        Map<String, Object> res = userNaming.execute("register", Map.of("username", "bob"));

        assertEquals("refused", res.get("outcome"));
    }

    @Test
    void registerAndLookupMissingUsernameAreErrors() {
        assertEquals("error",
                userNaming.execute("register", new HashMap<>()).get("outcome"));
        assertEquals("error",
                userNaming.execute("lookupByUsername", new HashMap<>()).get("outcome"));
    }

    @Test
    void setCredentialEnablesCheckAndReportsSet() {
        Map<String, Object> res = passwordAuth.execute("setCredential",
                Map.of("userId", "u1", "password", "pw"));

        assertEquals("SET", res.get("outcome"));
        assertEquals("u1", res.get("userId"));
        assertEquals("OK", passwordAuth.execute("check",
                Map.of("userId", "u1", "password", "pw")).get("outcome"));
    }

    @Test
    void setCredentialAndCheckMissingArgsAreErrors() {
        assertEquals("error", passwordAuth.execute("setCredential",
                Map.of("userId", "u1")).get("outcome"));
        assertEquals("error", passwordAuth.execute("check",
                Map.of("userId", "u1")).get("outcome"));
    }

    @Test
    void successfulCheckClearsAccumulatedFailures() {
        String userId = seedUser("alice", "secret");
        for (int i = 0; i < 4; i++) {
            passwordAuth.execute("check", Map.of("userId", userId, "password", "wrong"));
        }

        // The correct password clears the counter (clearAttempts).
        assertEquals("OK", passwordAuth.execute("check",
                Map.of("userId", userId, "password", "secret")).get("outcome"));

        // One more failure must be the first again, not the fifth: a leaked
        // counter would lock the account and reject the following success.
        Map<String, Object> res = passwordAuth.execute("check",
                Map.of("userId", userId, "password", "wrong"));
        assertEquals("BAD_PASSWORD", res.get("outcome"));
        assertEquals("OK", passwordAuth.execute("check",
                Map.of("userId", userId, "password", "secret")).get("outcome"));
    }

    @Test
    void setCredentialResetsAccumulatedFailures() {
        passwordAuth.execute("setCredential", Map.of("userId", "u2", "password", "pw"));
        for (int i = 0; i < 4; i++) {
            passwordAuth.execute("check", Map.of("userId", "u2", "password", "wrong"));
        }

        // Re-seeding clears failedAttempts (seedCredential); a leaked counter
        // would make the next failure the fifth and lock the account.
        passwordAuth.execute("setCredential", Map.of("userId", "u2", "password", "pw"));
        assertEquals("BAD_PASSWORD", passwordAuth.execute("check",
                Map.of("userId", "u2", "password", "wrong")).get("outcome"));
        assertEquals("OK", passwordAuth.execute("check",
                Map.of("userId", "u2", "password", "pw")).get("outcome"));
    }
}
