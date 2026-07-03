package com.example.app.concepts.passwordauth;

import com.example.app.ConceptTestBase;
import com.example.app.engine.RdfVocabulary;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

@DisplayName("PasswordAuthCheck")
class PasswordAuthCheckTest extends ConceptTestBase {

    private static final String USER_ID = "ada-0001";
    private static final String PASSWORD = "correct-horse-battery-staple";

    private PasswordAuthConcept concept;
    private int actionCounter = 0;
    private String lastActionIri;

    private String freshActionIri() {
        actionCounter++;
        lastActionIri = RdfVocabulary.ACTION_NODE_PREFIX + "check-test-" + actionCounter;
        return lastActionIri;
    }

    private void initConcept() {
        concept = new PasswordAuthConcept(log, bus);
    }

    private void writePendingInvocation(String userId, String password) {
        String actionIri = freshActionIri();
        log.update(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "INSERT DATA {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    <" + actionIri + "> :concept <" + PasswordAuthConcept.IRI + "> ;\n" +
            "                     :name    \"check\" ;\n" +
            "                     :input   _:inp ;\n" +
            "                     :flow    <" + flow.mintFlowToken() + "> .\n" +
            "    _:inp :userId   \"" + userId + "\" ;\n" +
            "          :password \"" + password + "\" .\n" +
            "  }\n" +
            "}\n");
    }

    private String readOutcome() {
        List<Map<String, String>> rows = log.select(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "SELECT ?_outcome WHERE {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    << <" + lastActionIri + "> :outcome ?_outcome >> :flow ?_flow .\n" +
            "  }\n" +
            "}\n");
        return rows.isEmpty() ? null : rows.get(0).get("_outcome");
    }

    private String readField(String fieldName) {
        List<Map<String, String>> rows = log.select(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "SELECT ?value WHERE {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    <" + lastActionIri + "> :" + fieldName + " ?value .\n" +
            "  }\n" +
            "}\n");
        return rows.isEmpty() ? null : rows.get(0).get("value");
    }

    @Nested
    @DisplayName("WhenCredentialsMatch")
    class WhenCredentialsMatch {

        @Test
        @DisplayName("shouldReturnOkWhenCredentialsMatch")
        void shouldReturnOkWhenCredentialsMatch() {
            // GIVEN: a credential is set for "ada"
            initConcept();
            concept.seedCredential(USER_ID, PASSWORD);
            writePendingInvocation(USER_ID, PASSWORD);

            // WHEN: check(ada-0001, correct-horse-battery-staple) is called
            concept.pollAll();

            // THEN: outcome is OK
            assertEquals("OK", readOutcome());
            assertEquals(USER_ID, readField("userId"));
        }
    }

    @Nested
    @DisplayName("WhenPasswordWrong")
    class WhenPasswordWrong {

        @Test
        @DisplayName("shouldReturnBadPasswordWhenPasswordWrong")
        void shouldReturnBadPasswordWhenPasswordWrong() {
            // GIVEN: a credential is set for "ada"
            initConcept();
            concept.seedCredential(USER_ID, PASSWORD);
            writePendingInvocation(USER_ID, "wrong-password");

            // WHEN: check(ada-0001, wrong-password) is called
            concept.pollAll();

            // THEN: outcome is BAD_PASSWORD
            assertEquals("BAD_PASSWORD", readOutcome());
            assertEquals(USER_ID, readField("userId"));
        }
    }

    @Nested
    @DisplayName("WhenAccountLocked")
    class WhenAccountLocked {

        @Test
        @DisplayName("shouldReturnLockedWhenAccountLocked")
        void shouldReturnLockedWhenAccountLocked() {
            // GIVEN: account locked after 5 failed attempts
            initConcept();
            concept.seedCredential(USER_ID, PASSWORD);
            for (int i = 0; i < 5; i++) {
                writePendingInvocation(USER_ID, "wrong");
                concept.pollAll();
            }
            writePendingInvocation(USER_ID, PASSWORD);

            // WHEN: check(ada-0001, correct-horse-battery-staple) is called (while locked)
            concept.pollAll();

            // THEN: outcome is LOCKED
            assertEquals("LOCKED", readOutcome());
            assertEquals(USER_ID, readField("userId"));
        }
    }
}
