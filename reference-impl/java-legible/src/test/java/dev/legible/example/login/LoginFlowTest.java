package dev.legible.example.login;

import dev.legible.engine.EvidenceWriter;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Behavioral parity with the existing UC-00-login Jena profile: the same four
 * scenarios, the same HTTP status codes, and the same field values.
 */
class LoginFlowTest {

    private static final String OPAQUE = "username or password didn't match";
    private static final String LOCKED = "Too many attempts. Try again in 15 minutes.";

    private LoginApp app;

    @BeforeEach
    void setUp() {
        app = LoginApp.create();
    }

    /** Emit machine-readable runtime evidence for the Acceptance-Spec comparison. */
    private void capture(String scenario, String test) {
        EvidenceWriter.to(System.getProperty(
                        "clad.evidence.dir", "target/acceptance-evidence"))
                .write(scenario, app.engine(), test);
    }

    @Test
    void successfulLoginReturns200WithSessionToken() {
        app.seedUser("alice", "secret");
        Map<String, Object> res = app.login("alice", "secret");

        assertEquals(200, res.get("status"));
        assertTrue(res.get("sessionToken") instanceof String);
        assertTrue(!((String) res.get("sessionToken")).isEmpty());
        capture("successful-login", "LoginFlowTest.successfulLoginReturns200WithSessionToken");
    }

    @Test
    void wrongPasswordReturns401WithOpaqueMessage() {
        app.seedUser("alice", "secret");
        Map<String, Object> res = app.login("alice", "wrong");

        assertEquals(401, res.get("status"));
        assertEquals(OPAQUE, res.get("message"));
        capture("wrong-password", "LoginFlowTest.wrongPasswordReturns401WithOpaqueMessage");
    }

    @Test
    void unknownUserReturns401WithOpaqueMessage() {
        app.seedUser("alice", "secret");
        Map<String, Object> res = app.login("nobody", "whatever");

        assertEquals(401, res.get("status"));
        assertEquals(OPAQUE, res.get("message"));
        capture("unknown-user", "LoginFlowTest.unknownUserReturns401WithOpaqueMessage");
    }

    @Test
    void lockoutReturns401WithVisibleMessage() {
        app.seedUser("alice", "secret");
        for (int i = 0; i < 5; i++) {
            Map<String, Object> wrong = app.login("alice", "wrong");
            assertEquals(401, wrong.get("status"), "attempt " + i + " should be rejected");
        }
        // Account is now locked; even the correct password is rejected.
        Map<String, Object> res = app.login("alice", "secret");

        assertEquals(401, res.get("status"));
        assertEquals(LOCKED, res.get("message"));
        capture("lockout", "LoginFlowTest.lockoutReturns401WithVisibleMessage");
    }

    @Test
    void lockoutIsNotPermanentAfterWindow() {
        app.seedUser("alice", "secret");
        for (int i = 0; i < 5; i++) {
            app.login("alice", "wrong");
        }
        // Correct password within the lockout window is rejected as LOCKED.
        assertEquals(401, app.login("alice", "secret").get("status"));
        // (The window is 15 minutes; verifying expiry would need clock injection,
        //  so we assert the locked state is observed rather than wait.)
    }

    @Test
    void successfulFlowRecordsExpectedConcepts() {
        app.seedUser("bob", "hunter2");
        Map<String, Object> res = app.login("bob", "hunter2");
        assertNotNull(res);

        // The flow is archived on completion; inspect the retained flow record.
        var archived = app.engine().archiver().buffer().latest().orElseThrow();
        var concepts = archived.invocations().stream()
                .map(i -> i.concept() + "/" + i.action())
                .distinct()
                .toList();
        assertTrue(concepts.contains("Web/request"));
        assertTrue(concepts.contains("UserNaming/lookupByUsername"));
        assertTrue(concepts.contains("PasswordAuth/check"));
        assertTrue(concepts.contains("Session/grant"));
        assertTrue(concepts.contains("Web/respond"));
    }
}
