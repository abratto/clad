package com.example.app.engine;

import jakarta.inject.Singleton;

import java.util.Map;

/**
 * Constructs typed response objects from the fields emitted by a completed
 * flow. Synchronizations declare the response shape in their sync spec as
 * {@code Web.respond(status, body={...})}. The engine stores those fields
 * in the action graph as RDF triples. This assembler reads them and returns
 * a typed DTO that Jackson serializes at the HTTP boundary.
 *
 * <p>Each flow type (login, refill, …) has its own assembly method.
 * The assembler sits at the transport boundary, not in the engine core.
 */
@Singleton
public class ResponseAssembler {

    /**
     * Returns the response body to be delivered by the controller. The given
     * {@code fields} map was read from the completed {@code Web/respond}
     * action's input triples in the action graph.
     *
     * <p>For simple flows the fields map is returned as-is — Micronaut's
     * Jackson serializer converts it to JSON. For flows that need typed
     * DTOs, subclass or extend this assembler with flow-specific methods.
     */
    public Map<String, String> assemble(String flowName, Map<String, String> fields) {
        return fields;
    }
}
