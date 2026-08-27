package com.example.app.architecture;

import com.example.app.ConceptTestBase;
import com.example.app.concepts.usernaming.UserNamingConcept;
import dev.clad.engine.RdfVocabulary;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationConfig;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Verifies hard-learned CLAD implementation rules.
 *
 * <p>R12: ConceptAgent.writeCompletion MUST write a plain {@code :outcome}
 *        triple to prevent reprocessing.
 * <p>R13: Jackson ObjectMapper MUST serialize null values.
 */
@MicronautTest
class CladRulesComplianceTest {

    @Inject
    ObjectMapper objectMapper;

    // -----------------------------------------------------------------------
    // R12 — writeCompletion prevents reprocessing
    // -----------------------------------------------------------------------

    /**
     * Verifies that after writeCompletion marks an action with a plain
     * {@code :outcome} triple, the concept agent does not re-process it.
     * Uses the in-memory ActionLog to write a completion, then confirm
     * the pending-invocation poll returns zero results.
     */
    @Test
    void writeCompletionPreventsReprocessing() {
        var log = new dev.clad.engine.ActionLog();
        var bus = new dev.clad.engine.CompletionBus();
        var flow = new dev.clad.engine.FlowManager(log, bus);
        var concept = new com.example.app.concepts.usernaming.UserNamingConcept(log, bus);

        concept.seedUser("r12-user", "r12-username");
        String actionIri = RdfVocabulary.ACTION_NODE_PREFIX + "r12-test";

        // Write a pending invocation
        log.update(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "INSERT DATA {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    <" + actionIri + "> :concept <" + UserNamingConcept.IRI + "> ;\n" +
            "                     :name    \"lookupByUsername\" ;\n" +
            "                     :input   _:inp ;\n" +
            "                     :flow    <" + flow.mintFlowToken() + "> .\n" +
            "    _:inp :username \"r12-username\" .\n" +
            "  }\n" +
            "}\n");

        // First poll: should find and process the invocation
        concept.pollAll();

        // Second poll: should find nothing (plain :outcome prevents reprocessing)
        List<Map<String, String>> rows = log.select(
            "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n" +
            "SELECT (COUNT(?a) AS ?c) WHERE {\n" +
            "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n" +
            "    ?a :concept <" + UserNamingConcept.IRI + "> ;\n" +
            "       :name \"lookupByUsername\" .\n" +
            "    FILTER NOT EXISTS { ?a :outcome ?_any }\n" +
            "  }\n" +
            "}\n");
        assertEquals("0", rows.get(0).get("c"),
                "R12: plain :outcome triple must prevent reprocessing");
    }

    // -----------------------------------------------------------------------
    // R13 — Jackson null serialization
    // -----------------------------------------------------------------------

    @Test
    void jacksonSerializesNullValues() {
        SerializationConfig config = objectMapper.getSerializationConfig();
        var inclusion = config.getDefaultPropertyInclusion().getValueInclusion();
        // R13: Jackson MUST serialize null values (Include.ALWAYS) so that
        // Conduit spec assertions like `jsonpath "$.user.bio" == null` hold.
        // The ObjectMapperCustomizer enforces this at the HTTP boundary.
        assertEquals(
                JsonInclude.Include.ALWAYS, inclusion,
                "R13: Jackson must serialize null values (Include.ALWAYS). "
                + "Current: " + inclusion + ".");
    }
}
