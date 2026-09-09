package com.example.app.infrastructure;

import com.example.app.api.LoginRequest;
import com.example.app.api.LoginFailureResponse;
import com.example.app.api.LoginSuccessResponse;
import com.example.app.api.ResponseAssembler;
import com.example.app.engine.LoginGateway;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Post;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.parameters.RequestBody;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.inject.Inject;

import java.util.Map;

/**
 * The Web bootstrap concept's adapter (R4): the only HTTP entry point.
 *
 * <p>Normalizes the request body, invokes the flow root through the engine
 * ({@code Web/request}), reads the authored {@code Web/respond} fields, and
 * translates the authored status code into transport output. Transport-only
 * by rule: it calls no business concept, reads no concept state, and decides
 * nothing about domain policy — the status code was authored by the declared
 * syncs (R3).
 */
@Tag(name = "web")
@Controller("/login")
public class WebController {

    private final LoginGateway gateway;
    private final ResponseAssembler assembler;

    @Inject
    public WebController(LoginGateway gateway, ResponseAssembler assembler) {
        this.gateway = gateway;
        this.assembler = assembler;
    }

    @Post(consumes = MediaType.APPLICATION_JSON, produces = MediaType.APPLICATION_JSON)
        @Operation(
            summary = "Authenticate a user",
            description = "Starts the login flow at the Web bootstrap boundary and returns the authored Web/respond result.")
        @RequestBody(
            required = true,
            description = "Login credentials normalized into the root Web/request action.",
            content = @Content(mediaType = MediaType.APPLICATION_JSON, schema = @Schema(implementation = LoginRequest.class)))
        @ApiResponse(
            responseCode = "200",
            description = "Login succeeded and a session token was granted.",
            content = @Content(mediaType = MediaType.APPLICATION_JSON, schema = @Schema(implementation = LoginSuccessResponse.class)))
        @ApiResponse(
            responseCode = "401",
            description = "Credential failure with a non-enumerating response body.",
            content = @Content(mediaType = MediaType.APPLICATION_JSON, schema = @Schema(implementation = LoginFailureResponse.class)))
    public HttpResponse<?> login(@Body LoginRequest body) {
        Map<String, Object> respond = gateway.login(
                body.username() == null ? "" : body.username(),
                body.password() == null ? "" : body.password());
        int status = ((Number) respond.get("status")).intValue();
        if (status == 200) {
            return HttpResponse.ok(assembler.success(respond));
        }
        return HttpResponse.unauthorized().body(assembler.failure(respond));
    }
}
