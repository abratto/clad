package com.example.app.engine;

import org.apache.jena.rdf.model.RDFNode;

import java.util.Collections;
import java.util.Map;

/**
 * Immutable value object representing a single action node in the RDF action log.
 * Every action — whether a root Web/request or a downstream concept invocation —
 * is captured as an {@code ActionRecord} after being written to the store.
 */
public record ActionRecord(
        String actionIri,
        String flowToken,
        String conceptIri,
        String actionName,
        Map<String, RDFNode> bindings
) {
    public ActionRecord {
        bindings = Collections.unmodifiableMap(bindings);
    }

    /**
     * Returns the string value of a named binding, or {@code null} if absent.
     */
    public String binding(String key) {
        RDFNode node = bindings.get(key);
        if (node == null) return null;
        if (node.isLiteral()) return node.asLiteral().getString();
        if (node.isResource()) return node.asResource().getURI();
        return node.toString();
    }
}
