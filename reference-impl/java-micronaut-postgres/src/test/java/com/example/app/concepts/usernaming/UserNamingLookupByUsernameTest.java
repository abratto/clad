package com.example.app.concepts.usernaming;

import com.example.app.PostgresConceptTestBase;
import dev.legible.engine.Region;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@DisplayName("UserNamingLookupByUsername (Postgres)")
class UserNamingLookupByUsernameTest extends PostgresConceptTestBase {

    private UserNamingConcept concept() {
        return new UserNamingConcept(store.region("UserNaming"));
    }

    private void seed(String userId, String username) {
        store.region("UserNaming").write(userId, "username", username);
    }

    @Nested
    @DisplayName("WhenUserExists")
    class WhenUserExists {

        @Test
        @DisplayName("shouldReturnFoundWithUserId")
        void shouldReturnFoundWithUserId() {
            seed("11111111-1111-1111-1111-111111111111", "ada");
            Map<String, Object> completion = concept()
                    .execute("lookupByUsername", Map.of("username", "ada"));

            assertEquals("FOUND", completion.get("outcome"));
            assertEquals("11111111-1111-1111-1111-111111111111", completion.get("userId"));
            assertEquals("ada", completion.get("username"));
        }
    }

    @Nested
    @DisplayName("WhenUserUnknown")
    class WhenUserUnknown {

        @Test
        @DisplayName("shouldRefuseWithoutEnumerating")
        void shouldRefuseWithoutStateException() {
            Map<String, Object> completion = concept()
                    .execute("lookupByUsername", Map.of("username", "nobody"));

            assertEquals("refused", completion.get("outcome"));
            assertTrue(String.valueOf(completion.get("message")).contains("nobody"));
        }
    }

    @Nested
    @DisplayName("WhenUsernameMissing")
    class WhenUsernameMissing {

        @Test
        @DisplayName("shouldReturnErrorOutcome")
        void shouldReturnErrorOutcome() {
            Map<String, Object> completion = concept().execute("lookupByUsername", Map.of());

            assertEquals("error", completion.get("outcome"));
        }
    }

    @Nested
    @DisplayName("WhenRegisteringDuplicateUsername")
    class WhenRegisteringDuplicateUsername {

        @Test
        @DisplayName("shouldRefuseRegistration")
        void shouldRefuseRegistration() {
            Region region = store.region("UserNaming");
            seed("aaa", "ada");
            UserNamingConcept concept = new UserNamingConcept(region);

            Map<String, Object> completion =
                    concept.execute("register", Map.of("username", "ada"));

            assertEquals("refused", completion.get("outcome"));
            assertFalse(String.valueOf(completion.get("message")).contains("aaa"));
        }
    }
}
