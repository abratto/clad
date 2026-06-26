package com.example.app.infrastructure;

import com.example.app.api.LoginFailureResponse;
import com.example.app.engine.ActionRecord;
import com.example.app.engine.FlowManager;
import com.example.app.engine.ResponseAssembler;
import com.example.app.engine.SyncDispatcher;
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
import reactor.core.publisher.Mono;

import com.example.app.api.LoginRequest;
import com.example.app.api.LoginSuccessResponse;

import java.util.Map;

/**
 * The Web bootstrap concept (R4): the only HTTP entry point.
 *
 * <p>Receives an HTTP request, calls {@link FlowManager#rootAction} to mint a
 * flow token and write the {@code Web/request} action node, then asks
 * {@link SyncDispatcher#awaitResponse} to drive concept and sync agents until
 * a {@code Web/respond} appears for that flow.
 *
 * <p>This class contains no domain branching — translation of outcomes happens
 * in declarative syncs (R3). It is intentionally named {@code WebController} to
 * preserve the architectural rule "no business class is named *Concept", and
 * its role corresponds to the {@code Web} concept of the WYSIWID architecture.
 */
@Tag(name = "web")
@Controller("/login")
public class WebController {

    private final FlowManager flowManager;
    private final SyncDispatcher syncDispatcher;

    @Inject
    public WebController(FlowManager flowManager, SyncDispatcher syncDispatcher) {
        this.flowManager = flowManager;
        this.syncDispatcher = syncDispatcher;
    }

    @Post(consumes = MediaType.APPLICATION_JSON, produces = MediaType.APPLICATION_JSON)
        @Operation(
            summary = "Authenticate a user",
            description = "Starts the CLAD login flow at the Web bootstrap boundary and waits for the authored Web/respond result.")
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
        @ApiResponse(
            responseCode = "500",
            description = "Dispatch loop timed out before a Web/respond action was authored.",
            content = @Content(mediaType = MediaType.TEXT_PLAIN, schema = @Schema(type = "string")))
    public Mono<HttpResponse<?>> login(@Body LoginRequest body) {
        ActionRecord root = flowManager.rootAction("login", Map.of(
                "username", body.username() == null ? "" : body.username(),
                "password", body.password() == null ? "" : body.password()
        ));
        return syncDispatcher.awaitResponse(root.flowToken());
    }
}
