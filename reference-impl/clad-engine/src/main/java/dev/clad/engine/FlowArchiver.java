package dev.clad.engine;

import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;

import java.io.ByteArrayOutputStream;

/**
 * Flushes completed flow action triples as N-Quads to a configurable
 * {@link FlowArchiveSink} before they are deleted from the in-memory
 * action log.
 *
 * <p>If the sink write fails, a {@link FlowArchiveException} is thrown
 * and the delete is skipped — triples remain in the in-memory action
 * log for retry.
 */
public class FlowArchiver {

    private final ActionLog actionLog;
    private final FlowArchiveSink sink;
    private final FlowArchiveBuffer buffer;
    private volatile boolean enabled = true;

    public FlowArchiver(ActionLog actionLog, FlowArchiveSink sink,
                        FlowArchiveBuffer buffer) {
        this.actionLog = actionLog;
        this.sink = sink;
        this.buffer = buffer;
    }

    public void setEnabled(boolean enabled) { this.enabled = enabled; }

    /**
     * Serializes a completed flow's triples as N-Quads, stores them in
     * the debug buffer, and flushes to the sink — all before deletion.
     */
    public void archiveFlow(String flowToken) {
        if (!enabled) return;

        try {
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

            // Store in debug buffer, then flush to sink
            if (buffer != null) buffer.store(flowToken, nquads.getBytes("UTF-8"));
            sink.write(flowToken, nquads);
        } catch (Exception e) {
            throw new FlowArchiveException(
                    "Failed to archive flow " + flowToken + " via sink '"
                    + sink.name() + "' — triples will NOT be deleted. "
                    + "Fix the sink and retry.", e);
        }
    }
}
