package com.example.app.api;

import jakarta.inject.Singleton;

import java.util.Map;

/**
 * Translates the authored {@code Web/respond} fields into typed DTOs at the
 * transport boundary. The response shape was declared by the syncs; this
 * class only maps the field names. No domain decisions are made here.
 */
@Singleton
public class ResponseAssembler {

    /** Typed success DTO from the Web/respond fields (200). */
    public LoginSuccessResponse success(Map<String, Object> fields) {
        return new LoginSuccessResponse(String.valueOf(fields.get("sessionToken")));
    }

    /** Typed failure DTO from the Web/respond fields (401). */
    public LoginFailureResponse failure(Map<String, Object> fields) {
        Object msg = fields.get("message");
        return new LoginFailureResponse(msg != null ? String.valueOf(msg) : "An error occurred");
    }
}
