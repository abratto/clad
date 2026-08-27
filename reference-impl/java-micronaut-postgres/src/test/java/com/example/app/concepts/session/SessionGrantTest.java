package com.example.app.concepts.session;

import com.example.app.PostgresConceptTestBase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@DisplayName("SessionGrant (Postgres)")
class SessionGrantTest extends PostgresConceptTestBase {

    private static final String USER_ID = "33333333-3333-3333-3333-333333333333";

    @Nested
    @DisplayName("WhenGrantingSession")
    class WhenGrantingSession {

        @Test
        @DisplayName("shouldMintSessionToken")
        void shouldMintSessionToken() {
            var concept = new SessionConcept(log, bus, dsl);
            writePendingInvocation(SessionConcept.IRI, "grant", Map.of("userId", USER_ID));

            concept.pollAll();

            assertEquals("GRANTED", readOutcome());
            assertNotNull(readField("sessionToken"));
            assertEquals(USER_ID, readField("userId"));
        }
    }
}
