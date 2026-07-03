package com.example.app.syncs;

import com.example.app.ConceptTestBase;
import com.example.app.concepts.passwordauth.PasswordAuthConcept;
import com.example.app.concepts.session.SessionConcept;
import com.example.app.engine.RdfVocabulary;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("WhenPasswordAuthCheckOkThenSessionGrantForLogin")
class WhenPasswordAuthCheckOkThenSessionGrantForLoginTest extends ConceptTestBase {

    private static final String FLOW_TOKEN = RdfVocabulary.FLOW_TOKEN_PREFIX + "grants-test-1";
    private static final String TRIGGER_IRI = RdfVocabulary.ACTION_NODE_PREFIX + "grants-trigger";
    private static final String USER_ID = "ada-0001";

    @Nested
    @DisplayName("WhenCheckOk")
    class WhenCheckOk {

        @Test
        @DisplayName("shouldFireSessionGrantWhenCheckOk")
        void shouldFireSessionGrantWhenCheckOk() {
            // GIVEN: a PasswordAuth.check completed with outcome OK and userId
            writeCompletedTrigger();
            var sync = new WhenPasswordAuthCheckOkThenSessionGrantForLogin(log);

            // WHEN: the sync is executed by the dispatcher
            sync.execute();

            // THEN: a Session.grant invocation is scheduled with the userId
            var scheduled = findPendingInvocation(SessionConcept.IRI, "grant");
            assertNotNull(scheduled, "Session.grant should be scheduled");
            assertEquals(USER_ID, scheduled.get("userId"));
        }
    }

    private void writeCompletedTrigger() {
        log.update(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "INSERT DATA {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    <" + TRIGGER_IRI + "> :concept <" + PasswordAuthConcept.IRI + "> ;\n" +
            "                     :name    \"check\" ;\n" +
            "                     :userId  \"" + USER_ID + "\" ;\n" +
            "                     :flow    <" + FLOW_TOKEN + "> .\n" +
            "    << <" + TRIGGER_IRI + "> :outcome \"OK\" >> :flow <" + FLOW_TOKEN + "> .\n" +
            "  }\n" +
            "}\n");
    }

    private Map<String, String> findPendingInvocation(String conceptIri, String actionName) {
        List<Map<String, String>> rows = log.select(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "SELECT ?action ?predicate ?value\n" +
            "WHERE {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    ?action :concept <" + conceptIri + "> ;\n" +
            "            :name    \"" + actionName + "\" ;\n" +
            "            :input   ?input ;\n" +
            "            :flow    <" + FLOW_TOKEN + "> .\n" +
            "    ?input ?predicate ?value .\n" +
            "  }\n" +
            "}\n");
        if (rows.isEmpty()) return null;
        Map<String, String> result = new java.util.LinkedHashMap<>();
        for (var row : rows) {
            result.put(row.get("predicate").substring(RdfVocabulary.ACTION_SCHEMA_IRI.length()),
                       row.get("value"));
        }
        return result;
    }
}
