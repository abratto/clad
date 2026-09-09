package com.example.app.concepts.session;

import com.example.app.PostgresConceptTestBase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@DisplayName("SessionGrant (Postgres)")
class SessionGrantTest extends PostgresConceptTestBase {

    private static final String USER_ID = "33333333-3333-3333-3333-333333333333";

    private SessionConcept concept() {
        return new SessionConcept(store.region("Session"));
    }

    @Nested
    @DisplayName("WhenGrantingSession")
    class WhenGrantingSession {

        @Test
        @DisplayName("shouldMintSessionTokenAndOpenAt")
        void shouldMintSessionToken() {
            Map<String, Object> completion = concept().execute("grant", Map.of("userId", USER_ID));

            assertEquals("GRANTED", completion.get("outcome"));
            String sessionId = String.valueOf(completion.get("sessionId"));
            assertNotNull(sessionId);
            assertTrue(!sessionId.isEmpty(), "sessionId must be minted, not empty");
            assertEquals(USER_ID, completion.get("userId"));

            Map<String, Object> opened = concept().execute("lookup", Map.of("sessionId", sessionId));
            assertEquals("ACTIVE", opened.get("outcome"));
            assertEquals(USER_ID, opened.get("userId"));
        }
    }

    @Nested
    @DisplayName("WhenSessionUnknown")
    class WhenSessionUnknown {

        @Test
        @DisplayName("shouldReportUnknown")
        void shouldReportUnknown() {
            Map<String, Object> completion = concept().execute("lookup", Map.of(
                    "sessionId", "no-such-session"));

            assertEquals("UNKNOWN", completion.get("outcome"));
        }
    }
}
