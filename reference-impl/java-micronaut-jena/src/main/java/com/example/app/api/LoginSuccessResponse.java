package com.example.app.api;

import io.micronaut.core.annotation.Introspected;
import io.swagger.v3.oas.annotations.media.Schema;

@Introspected
@Schema(name = "LoginSuccessResponse", description = "Successful login response authored by Web/respond.")
public record LoginSuccessResponse(
        @Schema(description = "Opaque session token minted by the Session concept.", example = "8f6b8b9b-6c7f-4e4b-8f59-dac6bd6c2b52")
        String sessionToken) {}