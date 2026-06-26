package com.example.app.concepts.user;

import com.example.app.ConceptTestBase;
import com.example.app.engine.ActionRecord;
import com.example.app.engine.FlowManager;
import com.example.app.engine.RdfVocabulary;
import org.apache.jena.rdf.model.RDFNode;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.apache.jena.graph.NodeFactory.createLiteralString;
import static org.apache.jena.rdf.model.ResourceFactory.createStringLiteral;
import static org.junit.jupiter.api.Assertions.*;

@DisplayName("UserLookupByUsername")
class UserLookupByUsernameTest extends ConceptTestBase {

    private UserConcept concept;
    private int actionCounter = 0;
    private String lastActionIri;

    private String freshActionIri() {
        actionCounter++;
        lastActionIri = RdfVocabulary.ACTION_NODE_PREFIX + "lookup-test-" + actionCounter;
        return lastActionIri;
    }

    private void initConcept() {
        concept = new UserConcept(log, bus);
    }

    private void writePendingInvocation(String username) {
        String actionIri = freshActionIri();
        log.update(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "INSERT DATA {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    <" + actionIri + "> :concept <" + UserConcept.IRI + "> ;\n" +
            "                     :name    \"lookupByUsername\" ;\n" +
            "                     :input   _:inp ;\n" +
            "                     :flow    <" + flow.mintFlowToken() + "> .\n" +
            "    _:inp :username \"" + username + "\" .\n" +
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
    @DisplayName("WhenUserExists")
    class WhenUserExists {

        @Test
        @DisplayName("shouldReturnUserIdWhenUserExists")
        void shouldReturnUserIdWhenUserExists() {
            // GIVEN: a user "ada" is registered
            initConcept();
            concept.seedUser("ada-0001", "ada");
            writePendingInvocation("ada");

            // WHEN: lookupByUsername("ada") is called
            concept.pollAll();

            // THEN: outcome is FOUND with the user's userId
            assertEquals("FOUND", readOutcome());
            assertNotNull(readField("userId"));
            assertEquals("ada-0001", readField("userId"));
        }
    }

    @Nested
    @DisplayName("WhenUserUnknown")
    class WhenUserUnknown {

        @Test
        @DisplayName("shouldReturnNotFoundWhenUserUnknown")
        void shouldReturnNotFoundWhenUserUnknown() {
            // GIVEN: no user named "nobody" exists
            initConcept();
            writePendingInvocation("nobody");

            // WHEN: lookupByUsername("nobody") is called
            concept.pollAll();

            // THEN: outcome is UNKNOWN
            assertEquals("UNKNOWN", readOutcome());
        }
    }
}
