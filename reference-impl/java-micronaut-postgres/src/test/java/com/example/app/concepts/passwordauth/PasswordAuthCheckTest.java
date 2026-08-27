package com.example.app.concepts.passwordauth;

import com.example.app.PostgresConceptTestBase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

@DisplayName("PasswordAuthCheck (Postgres)")
class PasswordAuthCheckTest extends PostgresConceptTestBase {

    private static final String USER_ID = "22222222-2222-2222-2222-222222222222";

    private PasswordAuthConcept concept;

    private void initConcept(String password) {
        concept = new PasswordAuthConcept(log, bus, dsl);
        concept.seedCredential(USER_ID, password);
    }

    @Nested
    @DisplayName("WhenCredentialsMatch")
    class WhenCredentialsMatch {

        @Test
        @DisplayName("shouldReturnOk")
        void shouldReturnOk() {
            initConcept("correct-password");
            writePendingInvocation(PasswordAuthConcept.IRI, "check",
                    Map.of("userId", USER_ID, "password", "correct-password"));

            concept.pollAll();

            assertEquals("OK", readOutcome());
        }
    }

    @Nested
    @DisplayName("WhenPasswordWrong")
    class WhenPasswordWrong {

        @Test
        @DisplayName("shouldReturnBadPassword")
        void shouldReturnBadPassword() {
            initConcept("correct-password");
            writePendingInvocation(PasswordAuthConcept.IRI, "check",
                    Map.of("userId", USER_ID, "password", "wrong-password"));

            concept.pollAll();

            assertEquals("BAD_PASSWORD", readOutcome());
        }
    }

    @Nested
    @DisplayName("WhenAccountLocked")
    class WhenAccountLocked {

        @Test
        @DisplayName("shouldReturnLockedAfterFiveFailures")
        void shouldReturnLockedAfterFiveFailures() {
            initConcept("correct-password");
            for (int i = 0; i < 5; i++) {
                writePendingInvocation(PasswordAuthConcept.IRI, "check",
                        Map.of("userId", USER_ID, "password", "wrong-password"));
                concept.pollAll();
            }
            writePendingInvocation(PasswordAuthConcept.IRI, "check",
                    Map.of("userId", USER_ID, "password", "correct-password"));
            concept.pollAll();

            assertEquals("LOCKED", readOutcome());
        }
    }
}
