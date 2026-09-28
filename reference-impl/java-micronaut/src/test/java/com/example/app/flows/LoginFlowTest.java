package com.example.app.flows;

import com.example.app.api.LoginRequest;
import dev.legible.engine.FlowRecord;
import dev.legible.engine.SyncEngine;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-end login flow over the full Micronaut stack (in-memory concept state
 * by default — see clad.storage). The in-memory FactStore is the default, so
 * this runs with no Docker; {@code DemoSeed} registers {@code ada}.
 *
 * <p>This is the profile-specific ADAPTER test (Stage 04c step 6): it starts at
 * the HTTP request, hits {@code WebController} -> {@code LoginGateway} ->
 * {@code SyncEngine} -> {@code WebConcept} + the business concepts/syncs, and
 * back to the HTTP response. Beyond status + body it asserts the runtime
 * flow-token chain (the {@code causedBySync} lineage) and that no action is left
 * stuck — proving the response came back through the authorised action/sync
 * chain, not by imperative controller branching (R1/R4/R5).
 */
@MicronautTest
class LoginFlowTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Inject
    SyncEngine engine;

    @Test
    void successfulLoginReturnsSessionToken() {
        HttpResponse<String> response = client.toBlocking().exchange(
                HttpRequest.POST("/login", new LoginRequest("ada", "correct-horse-battery-staple")),
                String.class);

        assertEquals(HttpStatus.OK, response.getStatus());
        assertTrue(response.body().contains("sessionToken"), "missing sessionToken in response body");
        assertEquals(
                List.of("Web.request", "UserNaming.lookupByUsername",
                        "PasswordAuth.check", "Session.grant", "Web.respond"),
                latestActionChain());
        assertNoStuckActions();
    }

    @Test
    void unknownUserReturns401() {
        HttpClientResponseException thrown = assertThrows(
                HttpClientResponseException.class,
                () -> client.toBlocking().exchange(
                        HttpRequest.POST("/login", new LoginRequest("nobody", "whatever")),
                        String.class));

        assertEquals(HttpStatus.UNAUTHORIZED, thrown.getStatus());
        // The refusal is decided by the guard action, before any write (R23):
        // no Session.grant appears in the chain.
        assertEquals(
                List.of("Web.request", "UserNaming.lookupByUsername", "Web.respond"),
                latestActionChain());
        assertNoStuckActions();
    }

    /** `concept.action` for every archived action of the most recent flow, in order. */
    @SuppressWarnings("unchecked")
    private List<String> latestActionChain() {
        FlowRecord record = engine.archiver().buffer().latest().orElseThrow(
                () -> new AssertionError("no archived flow — the request produced none"));
        List<Map<String, Object>> actions =
                (List<Map<String, Object>>) engine.debug().flow(record.flowId()).get("actions");
        return actions.stream()
                .filter(a -> a.get("outcome") != null)
                .map(a -> a.get("concept") + "." + a.get("action"))
                .toList();
    }

    private void assertNoStuckActions() {
        Map<String, Object> stuck = engine.debug().stuck();
        assertEquals(0, stuck.get("stuckCount"),
                "an action was committed with no completion: " + stuck);
    }
}
