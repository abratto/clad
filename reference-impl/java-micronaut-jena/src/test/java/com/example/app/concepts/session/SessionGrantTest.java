package com.example.app.concepts.session;

import com.example.app.ConceptTestBase;
import com.example.app.engine.RdfVocabulary;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("SessionGrant")
class SessionGrantTest extends ConceptTestBase {

    private SessionConcept concept;
    private int actionCounter = 0;
    private String lastActionIri;

    private String freshActionIri() {
        actionCounter++;
        lastActionIri = RdfVocabulary.ACTION_NODE_PREFIX + "grant-test-" + actionCounter;
        return lastActionIri;
    }

    private void initConcept() {
        concept = new SessionConcept(log, bus);
    }

    private void writePendingInvocation(String userId) {
        String actionIri = freshActionIri();
        log.update(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "INSERT DATA {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    <" + actionIri + "> :concept <" + SessionConcept.IRI + "> ;\n" +
            "                     :name    \"grant\" ;\n" +
            "                     :input   _:inp ;\n" +
            "                     :flow    <" + flow.mintFlowToken() + "> .\n" +
            "    _:inp :userId \"" + userId + "\" .\n" +
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
    @DisplayName("WhenGrantingSession")
    class WhenGrantingSession {

        @Test
        @DisplayName("shouldMintSessionTokenAndReturnUserId")
        void shouldMintSessionTokenAndReturnUserId() {
            initConcept();
            writePendingInvocation("user-0001");

            concept.pollAll();

            assertEquals("GRANTED", readOutcome());
            assertNotNull(readField("sessionToken"), "sessionToken must not be null");
            assertFalse(readField("sessionToken").isEmpty(), "sessionToken must not be empty");
            assertNotNull(readField("userId"));
            assertEquals("user-0001", readField("userId"));
        }
    }
}
