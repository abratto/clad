package com.example.app.engine;

import com.example.app.api.LoginFailureResponse;
import com.example.app.api.LoginSuccessResponse;
import jakarta.inject.Singleton;

import java.util.Map;

/**
 * Constructs typed response objects from the fields emitted by a completed
 * flow. Synchronizations declare the response shape in their sync spec as
 * {@code Web.respond(status, body={...})}. The engine stores those fields
 * in the action graph as RDF triples. This assembler reads them and returns
 * a typed DTO that Jackson serializes at the HTTP boundary.
 *
 * <p>Each flow type has its own assembly method. The assembler sits at the
 * transport boundary, not in the engine core. Transport adapters (REST,
 * GraphQL) call this to convert raw engine output into typed responses.
 */
@Singleton
public class ResponseAssembler {

    /**
     * Returns the response body for the given flow, typed when possible.
     *
     * @param flowName the CLAD flow name (e.g. {@code "login"})
     * @param fields   the field-value map from the completed {@code Web/respond} action
     * @return a typed DTO if a mapper exists, otherwise the raw fields map
     */
    public Object assemble(String flowName, Map<String, String> fields) {
        return switch (flowName) {
            case "login" -> new LoginSuccessResponse(fields.get("sessionToken"));
            default -> fields;
        };
    }

    /** Build a typed error DTO from field map. */
    public LoginFailureResponse toError(Map<String, String> fields) {
        String msg = fields.get("message");
        return new LoginFailureResponse(
                msg != null ? msg : "An error occurred");
    }
}
