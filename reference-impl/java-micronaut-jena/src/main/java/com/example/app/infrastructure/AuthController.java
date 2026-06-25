package com.example.app.infrastructure;

import com.example.app.api.LoginFailureResponse;
import com.example.app.api.LoginRequest;
import com.example.app.api.LoginSuccessResponse;
import com.example.app.engine.ActionRecord;
import com.example.app.engine.FlowManager;
import com.example.app.engine.ResponseAssembler;
import com.example.app.engine.SyncDispatcher;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
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

import java.util.Map;

/**
 * REST transport adapter for the login flow. Translates HTTP → CLAD engine →
 * typed DTO, demonstrating the ports-and-adapters pattern.
 *
 * <p>Calls {@link FlowManager#rootAction} → {@link SyncDispatcher#awaitResponse}
 * → {@link ResponseAssembler#assemble}. Contains zero business logic (R4).
 */
@Tag(name = "auth")
@Controller("/api")
public class AuthController {

    private final FlowManager flowManager;
    private final SyncDispatcher syncDispatcher;
    private final ResponseAssembler responseAssembler;

    @Inject
    public AuthController(FlowManager flowManager, SyncDispatcher syncDispatcher,
                          ResponseAssembler responseAssembler) {
        this.flowManager = flowManager;
        this.syncDispatcher = syncDispatcher;
        this.responseAssembler = responseAssembler;
    }

    @SuppressWarnings("unchecked")
    private Mono<HttpResponse<?>> assemble(String flowName, Mono<HttpResponse<?>> responseMono) {
        return responseMono.map(resp -> {
            if (resp.body() instanceof Map) {
                Map<String, String> fields = (Map<String, String>) resp.body();
                io.micronaut.http.MutableHttpResponse<Object> result;
                if (resp.getStatus() == HttpStatus.OK) {
                    result = io.micronaut.http.HttpResponse.ok(
                            responseAssembler.assemble(flowName, fields));
                } else {
                    result = io.micronaut.http.HttpResponse.status(resp.getStatus())
                            .body(responseAssembler.toError(fields));
                }
                String flowToken = resp.getHeaders().get("X-Flow-Token");
                if (flowToken != null) result.header("X-Flow-Token", flowToken);
                return result;
            }
            return resp;
        });
    }

    @Post(uri = "/login", consumes = MediaType.APPLICATION_JSON, produces = MediaType.APPLICATION_JSON)
    @Operation(summary = "Authenticate with username and password (REST)",
            operationId = "apiLogin",
            description = "Starts the Login flow via the CLAD engine. Same engine, same flow tokens as the legacy /login endpoint and GraphQL surface.")
    @RequestBody(required = true, content = @Content(mediaType = MediaType.APPLICATION_JSON,
            schema = @Schema(implementation = LoginRequest.class)))
    @ApiResponse(responseCode = "200", description = "Login succeeded.",
            content = @Content(schema = @Schema(implementation = LoginSuccessResponse.class)))
    @ApiResponse(responseCode = "401", description = "Credential failure.",
            content = @Content(schema = @Schema(implementation = LoginFailureResponse.class)))
    public Mono<HttpResponse<?>> login(@Body LoginRequest body) {
        ActionRecord root = flowManager.rootAction("login", Map.of(
                "username", body.username() == null ? "" : body.username(),
                "password", body.password() == null ? "" : body.password()
        ));
        return assemble("login", syncDispatcher.awaitResponse(root.flowToken()));
    }
}
