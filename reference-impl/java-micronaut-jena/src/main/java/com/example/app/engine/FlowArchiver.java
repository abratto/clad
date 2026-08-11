package com.example.app.engine;

import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.ByteArrayOutputStream;

/**
 * Flushes completed flow action triples as N-Quads-in-JSON log entries
 * before they are deleted from the in-memory action log.
 *
 * <p>Each flow's triples are serialized as a single line-delimited N-Quads
 * string embedded in a structured JSON log. The log aggregator indexes
 * {@code flow_token} and {@code event_type} for operational correlation.
 * Rehydration: extract the {@code rdf_payload} field and pipe into
 * Jena RIOT or {@code tdb2.tdbloader}.
 */
public class FlowArchiver {

    private static final Logger LOG = LoggerFactory.getLogger(FlowArchiver.class);

    private final ActionLog actionLog;
    private volatile boolean enabled = true;

    public FlowArchiver(ActionLog actionLog) {
        this.actionLog = actionLog;
    }

    public void setEnabled(boolean enabled) { this.enabled = enabled; }

    /**
     * Archives a completed flow's triples before they are deleted.
     * Reads all triples for the given flow token from the action graph,
     * serializes them as N-Quads, and writes a structured log entry.
     */
    public void archiveFlow(String flowToken) {
        if (!enabled) return;

        try {
            // Read all triples for this flow token from the action graph
            String query = "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n"
                    + "CONSTRUCT { ?s ?p ?o }\n"
                    + "WHERE {\n"
                    + "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n"
                    + "    ?a :flow <" + flowToken + "> .\n"
                    + "    { ?a ?p ?o . BIND(?a AS ?s) }\n"
                    + "    UNION { ?a :input ?s . ?s ?p ?o }\n"
                    + "    UNION { << ?a :outcome ?outcome >> ?p ?v .\n"
                    + "             BIND(<< ?a :outcome ?outcome >> AS ?s)\n"
                    + "             BIND(?v AS ?o) }\n"
                    + "  }\n"
                    + "}";

            org.apache.jena.rdf.model.Model model = actionLog.construct(query);
            if (model.isEmpty()) return;

            ByteArrayOutputStream out = new ByteArrayOutputStream();
            RDFDataMgr.write(out, model, Lang.NQ);
            String nquads = out.toString("UTF-8");

            // JSON-log: N-Quads in an opaque string payload
            String logEntry = "{\"timestamp\":\"" + java.time.Instant.now()
                    + "\",\"level\":\"INFO\",\"flow_token\":\"" + flowToken
                    + "\",\"event_type\":\"flow_archived\",\"rdf_payload\":"
                    + toJsonString(nquads) + "}";

            LOG.info("{}", logEntry);
        } catch (Exception e) {
            LOG.warn("Failed to archive flow {} to log: {}", flowToken, e.getMessage());
        }
    }

    private static String toJsonString(String s) {
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r")
                .replace("\t", "\\t") + "\"";
    }
}
