package com.example.app.concepts.usernaming;

import com.example.app.PostgresConceptTestBase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@DisplayName("UserNamingLookupByUsername (Postgres)")
class UserNamingLookupByUsernameTest extends PostgresConceptTestBase {

    private UserNamingConcept concept;

    private void initConcept() {
        concept = new UserNamingConcept(log, bus, dsl);
    }

    @Nested
    @DisplayName("WhenUserExists")
    class WhenUserExists {

        @Test
        @DisplayName("shouldReturnUserIdWhenUserExists")
        void shouldReturnUserIdWhenUserExists() {
            initConcept();
            concept.seedUser("11111111-1111-1111-1111-111111111111", "alice");
            writePendingInvocation(UserNamingConcept.IRI, "lookupByUsername", Map.of("username", "alice"));

            concept.pollAll();

            assertEquals("FOUND", readOutcome());
            assertNotNull(readField("username"));
            assertEquals("alice", readField("username"));
            assertNotNull(readField("userId"));
            assertEquals("11111111-1111-1111-1111-111111111111", readField("userId"));
        }
    }

    @Nested
    @DisplayName("WhenUserUnknown")
    class WhenUserUnknown {

        @Test
        @DisplayName("shouldRefuseWhenUserUnknown")
        void shouldRefuseWhenUserUnknown() {
            initConcept();
            writePendingInvocation(UserNamingConcept.IRI, "lookupByUsername", Map.of("username", "nobody"));

            concept.pollAll();

            assertEquals("refused", readOutcome());
            assertEquals("username not found: nobody", readField("refusalReason"));
        }
    }
}
