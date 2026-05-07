package com.example.app.infrastructure;

import com.example.app.engine.ActionRecord;
import com.example.app.engine.FlowManager;
import com.example.app.engine.SyncDispatcher;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Post;
import jakarta.inject.Inject;
import reactor.core.publisher.Mono;

import com.example.app.api.LoginRequest;

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
    public Mono<HttpResponse<?>> login(@Body LoginRequest body) {
        ActionRecord root = flowManager.rootAction("login", Map.of(
                "username", body.username() == null ? "" : body.username(),
                "password", body.password() == null ? "" : body.password()
        ));
        return syncDispatcher.awaitResponse(root.flowToken());
    }
}
