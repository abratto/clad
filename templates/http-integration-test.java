// Template for Stage 04c step 6 — profile-specific end-to-end ADAPTER test.
// Derived from: ../01b_chain-table/output/<scenario>-chain.md   (route, statuses)
//               ../03_syncs/output/*.sync.md                     (response literals)
//               ../04b_contract/output/<Name>.contract.md        (response shapes)
//               ../../../_config/package-and-layout.md           (package, source roots)
//
// This is NOT the flow test. The flow test asserts the action TOKEN
// CHAIN (request -> guards -> write -> respond) through the engine. This test
// asserts the TRANSPORT round-trip: an HTTP request hits the controller, the
// bootstrap (`Web`) concept routes it, the business concepts/syncs run, and an
// HTTP response comes back with the authored status and body shape — plus the
// persisted state (state round-tripping).
//
// Derivation rules (cross-reference with the 01b chain table):
//   Route + verb + request DTO   <- row 1 `Web/request[POST /route]`
//   Success status + body fields <- terminal `Web.respond[2xx]` row
//   Failure status + envelope    <- refusal `Web.respond[4xx]` rows (one per)
//   State round-trip assertions  <- the writing action's completion payload
//
// Profile adaptation: this sample targets the java-micronaut profile
// (@MicronautTest + injected HttpClient, embedded server, no Docker for the
// in-memory binding). For another profile, keep the assertions and replace the
// harness: java-legible/plain builds the app directly (e.g. `App.create()` /
// the gateway) and calls the flow, as `reference-impl/java-legible/.../flows/`.
//
// At Stage 04c the app has no business implementation yet, so this test is
// `@Disabled`. Remove `@Disabled` once the implementation lands (04d/04e);
// Stage 05 (`verify_adapter_test.py --require-enabled`) requires it enabled.

package <APP_PACKAGE_ROOT>.flows;

import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-end adapter test for UC-XX — <feature name>.
 *
 * POST /<route> -> <Feature>Controller -> <Feature>Gateway -> SyncEngine
 *   -> WebConcept + <business concepts>/<syncs> -> HTTP response.
 *
 * Uses the profile's concept-state binding (in-memory by default; the durable
 * binding is exercised by the persistence tests). Remove @Disabled once 04d/04e land.
 */
@Disabled("acceptance/adapter test — enable once 04d/04e land")
@MicronautTest
class <Feature>HttpIntegrationTest {

    @Inject
    @Client("/")
    HttpClient client;

    // Happy path: authored success status + response body shape (step 6).
    @Test
    void <scenario>ReturnsAuthoredSuccessResponse() {
        HttpResponse<String> response = client.toBlocking().exchange(
                HttpRequest.POST("/<route>", new <Feature>Request(<happy-path args>)),
                String.class);

        assertEquals(HttpStatus.CREATED, response.getStatus()); // <- from Web.respond[201]
        assertTrue(response.body().contains("<success-field>"),
                   "missing <success-field> in response body");
        // State round-trip: the writing action's completion payload is visible
        // in the response (and persisted in the concept's region).
    }

    // Failure envelope: each distinct refusal has its own status (R9/R12).
    @Test
    void <scenario>RefusesWithAuthoredFailureEnvelope() {
        HttpClientResponseException thrown = assertThrows(
                HttpClientResponseException.class,
                () -> client.toBlocking().exchange(
                        HttpRequest.POST("/<route>", new <Feature>Request(<refusal args>)),
                        String.class));

        assertEquals(HttpStatus.BAD_REQUEST, thrown.getStatus()); // <- from Web.respond[400]
        assertTrue(thrown.getResponse().getBody(String.class).orElse("")
                       .contains("<error-message>"),
                   "missing authored failure envelope");
    }

    // Optional: assert the runtime flow-token chain, not only the HTTP surface.
    // The canonical debug surface (java-micronaut DebugApi, java-legible
    // engine.debug()) exposes committed actions with their causedBySync lineage.
    // @Test
    // void <scenario>ReachesTransportThroughTheAuthorisedChain() {
    //     ... read the flow archive for the request and assert the token order
    //     Web.request[ROUTED] -> <guards> -> <write> -> Web.respond[<status>].
    // }
}
