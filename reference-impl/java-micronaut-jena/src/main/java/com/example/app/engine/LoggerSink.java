package com.example.app.engine;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Default sink — writes N-Quads-in-JSON log entries to SLF4J. The log
 * aggregator (Splunk, Datadog, ELK) indexes flow_token and event_type
 * for operational correlation. Rehydrate via
 * {@code jq -r '.rdf_payload' | riot --syntax=NQ}.
 */
public class LoggerSink implements FlowArchiveSink {

    private static final Logger LOG = LoggerFactory.getLogger("clad.flow-archive");

    @Override
    public void write(String flowToken, String nquads) {
        String logEntry = "{\"timestamp\":\"" + java.time.Instant.now()
                + "\",\"level\":\"INFO\",\"flow_token\":\"" + flowToken
                + "\",\"event_type\":\"flow_archived\",\"rdf_payload\":"
                + toJsonString(nquads) + "}";
        LOG.info("{}", logEntry);
    }

    @Override
    public String name() { return "logger"; }

    private static String toJsonString(String s) {
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r")
                .replace("\t", "\\t") + "\"";
    }
}
