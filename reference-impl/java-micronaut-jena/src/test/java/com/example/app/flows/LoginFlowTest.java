package com.example.app.flows;

import com.example.app.api.LoginRequest;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Outside-loop tests for UC-00-login.
 *
 * <p>Each test corresponds one-to-one with a scenario in
 * {@code features/UC-00-login/stages/01_usecase/output/usecase.md} and the
 * predicted token chain in
 * {@code features/UC-00-login/stages/04_implement/04c_flow-tests/output/login-flow-test.md}.
 *
 * <p>The Micronaut test boots the full embedded server, including the
 * {@code Application.DemoSeed} startup hook that registers user "ada" with the
 * password used here.
 */
@MicronautTest
class LoginFlowTest {

    private static final String FAILURE_MESSAGE = "username or password didn't match";

    @Inject
    @Client("/")
    HttpClient client;

    @Test
    void successful_login_grants_session_and_returns_token() {
        HttpResponse<String> resp = client.toBlocking().exchange(
                HttpRequest.POST("/login",
                        new LoginRequest("ada", "correct-horse-battery-staple")),
                String.class);
        assertEquals(HttpStatus.OK, resp.getStatus());
        String body = resp.body();
        assertNotNull(body, "body must be present");
        assertTrue(body.contains("\"sessionToken\""),
                "body must contain sessionToken; got " + body);
    }

    @Test
    void wrong_password_returns_401_with_non_enumerating_message() {
        HttpClientResponseException ex = assertThrows401(() ->
                client.toBlocking().exchange(
                        HttpRequest.POST("/login",
                                new LoginRequest("ada", "wrong")),
                        String.class));
        assertTrue(bodyOf(ex).contains(FAILURE_MESSAGE),
                "body must contain failure message; got " + bodyOf(ex));
    }

    @Test
    void unknown_user_returns_same_message_as_wrong_password() {
        HttpClientResponseException ex = assertThrows401(() ->
                client.toBlocking().exchange(
                        HttpRequest.POST("/login",
                                new LoginRequest("nobody", "anything")),
                        String.class));
        assertTrue(bodyOf(ex).contains(FAILURE_MESSAGE),
                "body must contain failure message; got " + bodyOf(ex));
    }

    private static HttpClientResponseException assertThrows401(Runnable r) {
        try {
            r.run();
        } catch (HttpClientResponseException e) {
            assertEquals(HttpStatus.UNAUTHORIZED, e.getStatus(),
                    "expected 401; got " + e.getStatus());
            return e;
        }
        throw new AssertionError("expected HttpClientResponseException");
    }

    private static String bodyOf(HttpClientResponseException ex) {
        return ex.getResponse().getBody(String.class).orElse("");
    }
}
