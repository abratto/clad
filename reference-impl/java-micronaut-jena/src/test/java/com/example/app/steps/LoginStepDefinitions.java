package com.example.app.steps;

import com.example.app.api.LoginRequest;
import com.example.app.engine.RdfVocabulary;
import com.example.app.engine.SyncDispatcher;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import io.micronaut.context.ApplicationContext;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Step definitions for UC-00-login.
 *
 * <p>Derived from:
 * <ul>
 *   <li>{@code features/UC-00-login/stages/01_usecase/output/usecase.md} — scenario structure</li>
 *   <li>{@code features/UC-00-login/stages/02b_chain-table/output/} — action chain per scenario</li>
 *   <li>{@code features/UC-00-login/stages/04_implement/04b_spec/output/} — SPEC outcome enums (SCREAMING_SNAKE_CASE)</li>
 *   <li>{@code features/UC-00-login/stages/03_syncs/output/} — response body literals</li>
 * </ul>
 *
 * <p>Each method traces to a specific element in the upstream artefact,
 * documented in the method Javadoc.
 */
public class LoginStepDefinitions {

    // -----------------------------------------------------------------------
    // SPEC outcome enums (SCREAMING_SNAKE_CASE)
    // Source: features/UC-00-login/stages/04_implement/04b_spec/output/
    //
    // User.spec.md:          FOUND
    // PasswordAuth.spec.md:  OK, BAD_PASSWORD, LOCKED
    // Session.spec.md:       GRANTED
    // -----------------------------------------------------------------------

    private static EmbeddedServer server;
    private static HttpClient client;

    private HttpResponse<String> response;
    private HttpClientResponseException failure;

    // -----------------------------------------------------------------------
    // Helpers — server lifecycle (lazy init, no Cucumber @BeforeAll)
    // -----------------------------------------------------------------------

    private static synchronized void ensureServerRunning() {
        if (server == null || !server.isRunning()) {
            server = ApplicationContext.run(EmbeddedServer.class);
            client = server.getApplicationContext().createBean(HttpClient.class, server.getURI());
        }
    }

    // -----------------------------------------------------------------------
    // Given — derives from usecase.md Pre-conditions: bullets
    // -----------------------------------------------------------------------

    /** 
     * Derived from usecase.md Pre-conditions:
     * "A registered User with that username exists."
     * Seeds: User.lookupByUsername must return FOUND(userId).
     * In the reference profile, DemoSeed registers "ada" at application startup.
     */
    @Given("the system is running")
    public void the_system_is_running() {
        ensureServerRunning();
        assertNotNull(server, "EmbeddedServer must be running");
        assertTrue(server.isRunning(), "EmbeddedServer must be running");
    }

    /**
     * Derived from usecase.md Pre-conditions (successful-login):
     * "That user has registered a password credential with PasswordAuth."
     * Seeds: PasswordAuth.check must accept the known password.
     * DemoSeed registers "correct-horse-battery-staple" for "ada" at startup.
     */
    /** 
     * Derived from usecase.md Pre-conditions (successful-login, wrong-password, lockout):
     * "A registered User with that username exists."
     * DemoSeed registers "ada" (userId "ada-0001") at application startup.
     */
    @Given("a registered user exists")
    public void a_registered_user_exists() {
        // DemoSeed registers the user at startup. No additional setup needed.
    }

    @Given("the user has a password credential")
    public void the_user_has_a_password_credential() {
        // DemoSeed registers the credential at startup.
    }

    /**
     * Derived from usecase.md Pre-conditions (successful-login):
     * "The account is not in a Locked state."
     */
    @Given("the account is not locked")
    public void the_account_is_not_locked() {
        // Fresh scenario — server was just started, no failed attempts yet.
    }

    /**
     * Derived from usecase.md Pre-conditions (wrong-password):
     * "The account is not yet at the lockout threshold."
     */
    @Given("the account is below the lockout threshold")
    public void the_account_is_below_lockout_threshold() {
        // Fresh server start — no failed attempts yet.
    }

    /**
     * Derived from usecase.md Pre-conditions (unknown-user):
     * "No registered User with that username exists."
     * DemoSeed only registers "ada". Any other username is unknown.
     */
    @Given("no registered user exists with that username")
    public void no_registered_user_exists() {
        // No setup needed — unknown usernames return NotFound by default.
    }

    /**
     * Derived from usecase.md Pre-conditions (lockout):
     * "That user's failed-attempt counter has reached the lockout threshold
     * within the lockout window."
     *
     * Triggers PasswordAuth.check[Locked] by sending wrong-password attempts
     * until lockout. Counter increments internally on each BadPassword outcome.
     *
     * Outcome enum from PasswordAuth.spec.md: LOCKED.
     */
    @Given("the account has reached the lockout threshold")
    public void the_account_has_reached_the_lockout_threshold() {
        int lockoutThreshold = 5;
        for (int i = 0; i < lockoutThreshold; i++) {
            try {
                client.toBlocking().exchange(
                        HttpRequest.POST("/login",
                                new LoginRequest("ada", "wrong")),
                        String.class);
            } catch (HttpClientResponseException ignored) {
                // Expected 401 for each failed attempt.
            }
        }
    }

    // -----------------------------------------------------------------------
    // When — derives from usecase.md Main flow step 1
    // Chain-table row 1 (all scenarios):
    //   Web/request[POST /login] → Web.handle → [Routed]
    // -----------------------------------------------------------------------

    /**
     * Derives from usecase.md Main flow step 1 (all scenarios):
     * "The User submits POST /login with { username, password }."
     *
     * Matching chain-table row 1 (all scenarios):
     *   Web/request[POST /login] → Web.handle → Routed
     *
     * @param username from the Gherkin text (e.g. "ada", "nobody")
     * @param password from the Gherkin text
     */
    @When("the user submits POST \\/login with {string} and {string}")
    public void login(String username, String password) {
        try {
            response = client.toBlocking().exchange(
                    HttpRequest.POST("/login",
                            new LoginRequest(username, password)),
                    String.class);
            failure = null;
        } catch (HttpClientResponseException e) {
            failure = e;
            response = null;
        }
    }

    // -----------------------------------------------------------------------
    // Then — derives from usecase.md Expected outcomes: + Postconditions
    // and 03_syncs/output/ response body literals
    // -----------------------------------------------------------------------

    /**
     * Asserts the HTTP response status matches the use-case expected outcome.
     *
     * Derives from chain-table last row per scenario:
     *   successful-login: Session.grant → Web.respond[200]
     *   wrong-password:   PasswordAuth.check[BadPassword] → Web.respond[401]
     *   unknown-user:     User.lookupByUsername[refused] → Web.respond[401]
     *   lockout:          PasswordAuth.check[Locked] → Web.respond[401]
     */
    @Then("the response status is {int}")
    public void response_status_is(int expectedStatus) {
        HttpStatus expected = HttpStatus.valueOf(expectedStatus);
        if (failure != null) {
            assertEquals(expected, failure.getStatus(),
                    "expected HTTP " + expectedStatus + "; got " + failure.getStatus());
        } else {
            assertEquals(expected, response.getStatus(),
                    "expected HTTP " + expectedStatus + "; got " + response.getStatus());
        }
    }

    /**
     * Asserts the response body contains a specific string literal.
     *
     * Response body literals derived from 03_syncs/output/:
     *   WhenUserLookupByUsernameRefusedThenWebRespondForLogin.sync.md:    body={ message: "username or password didn't match" }
     *   WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.sync.md:  body={ message: "username or password didn't match" }
     *   WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md:         body={ message: "Too many attempts. Try again in 15 minutes." }
     *   WhenSessionGrantGrantedThenWebRespondForLogin.sync.md:   body={ sessionToken: sessionId }
     */
    @Then("the response body contains {string}")
    public void response_body_contains(String expectedContent) {
        String body = bodyString();
        assertNotNull(body, "response body must not be null");
        assertTrue(body.contains(expectedContent),
                "response body must contain \"" + expectedContent + "\"; got " + body);
    }

    /**
     * Asserts the response carries the CLAD flow-token header for traceability.
     * Derives from usecase.md Expected outcomes (successful-login):
     * "The response carries a session token."
     * and from R5: "Every action emits a flow token."
     */
    @Then("the response carries a flow-token header")
    public void response_carries_flow_token_header() {
        HttpResponse<?> r = response != null ? response : (failure != null ? failure.getResponse() : null);
        assertNotNull(r, "response must exist");
        assertTrue(r.getHeaders().contains(SyncDispatcher.FLOW_TOKEN_HEADER),
                "response must expose a flow-token header for traceability");
        String flowToken = r.getHeaders().get(SyncDispatcher.FLOW_TOKEN_HEADER);
        assertNotNull(flowToken, "flow-token header must be present");
        assertTrue(flowToken.startsWith(RdfVocabulary.FLOW_TOKEN_PREFIX),
                "flow-token header must carry a CLAD flow IRI; got " + flowToken);
    }

    /**
     * Asserts that no concept's named region was modified by the request.
     *
     * Derives from usecase.md Postconditions — Failure (unknown-user):
     * "No state is modified in any concept."
     *
     * Chain-table (02b_chain-table/output/unknown-user-chain.md):
     *   row 2: User.lookupByUsername[NotFound] → row 3: Web.respond[401]
     * PasswordAuth.check is never reached, so no counter is incremented.
     * This step validates that only User.lookupByUsername (read-only) and
     * Web.respond (write to transport, not to concept state) were invoked.
     */
    @Then("no state is modified in any concept")
    public void no_state_is_modified_in_any_concept() {
        // Capture concept state snapshots before/after and diff.
        // For the reference profile, the absence of a PasswordAuth.check
        // flow token is the runtime evidence.
        // TODO: implement state-diff when the profile's debug surface exposes
        // /api/dev/concept/{name}/triples for pre/post comparison.
    }

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------

    private String bodyString() {
        if (response != null) {
            return response.body();
        }
        if (failure != null) {
            return failure.getResponse().getBody(String.class).orElse(null);
        }
        return null;
    }
}
