package com.example.app.api;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(name = "LoginFailureResponse", description = "Credential failure response authored by Web/respond.")
public record LoginFailureResponse(
        @Schema(description = "Non-enumerating credential failure message.", example = "username or password didn't match")
        String message) {}