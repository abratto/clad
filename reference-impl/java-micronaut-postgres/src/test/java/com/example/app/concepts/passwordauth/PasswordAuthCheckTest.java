package com.example.app.concepts.passwordauth;

import com.example.app.PostgresConceptTestBase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@DisplayName("PasswordAuthCheck (Postgres)")
class PasswordAuthCheckTest extends PostgresConceptTestBase {

    private static final String USER_ID = "22222222-2222-2222-2222-222222222222";

    private PasswordAuthConcept concept() {
        return new PasswordAuthConcept(store.region("PasswordAuth"));
    }

    private PasswordAuthConcept seeded(String password) {
        PasswordAuthConcept concept = concept();
        concept.seedCredential(USER_ID, password);
        return concept;
    }

    @Nested
    @DisplayName("WhenCredentialsMatch")
    class WhenCredentialsMatch {

        @Test
        @DisplayName("shouldReturnOkAndKeepCredential")
        void shouldReturnOk() {
            PasswordAuthConcept concept = seeded("correct-password");

            Map<String, Object> completion = concept.execute("check", Map.of(
                    "userId", USER_ID,
                    "password", "correct-password"));

            assertEquals("OK", completion.get("outcome"));
            assertEquals(USER_ID, completion.get("userId"));
            assertTrue(!store.region("PasswordAuth").read(USER_ID, "passwordHash").isEmpty());
        }
    }

    @Nested
    @DisplayName("WhenPasswordWrong")
    class WhenPasswordWrong {

        @Test
        @DisplayName("shouldReturnBadPasswordAndCountFailure")
        void shouldReturnBadPassword() {
            PasswordAuthConcept concept = seeded("correct-password");

            Map<String, Object> completion = concept.execute("check", Map.of(
                    "userId", USER_ID,
                    "password", "wrong-password"));

            assertEquals("BAD_PASSWORD", completion.get("outcome"));
            assertEquals("1", store.region("PasswordAuth")
                    .read(USER_ID, "failedAttempts").iterator().next());
        }
    }

    @Nested
    @DisplayName("WhenAccountLocked")
    class WhenAccountLocked {

        @Test
        @DisplayName("shouldReturnLockedWhenThresholdReached")
        void shouldReturnLocked() {
            PasswordAuthConcept concept = seeded("correct-password");
            for (int i = 0; i < 5; i++) {
                concept.execute("check", Map.of(
                        "userId", USER_ID,
                        "password", "incorrect"));
            }

            Map<String, Object> completion = concept.execute("check", Map.of(
                    "userId", USER_ID,
                    "password", "correct-password"));

            assertEquals("LOCKED", completion.get("outcome"));
            assertTrue(store.region("PasswordAuth").read(USER_ID, "lockedUntil")
                    .iterator().next() != null);
        }
    }
}
