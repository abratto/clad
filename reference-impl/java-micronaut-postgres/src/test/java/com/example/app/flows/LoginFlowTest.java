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
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-end login flow over the full Micronaut + Postgres stack. The action
 * log is in-memory; concept state (users, credentials, sessions) is Postgres
 * (see {@code TestPostgresDataSourceFactory}). The DemoSeed registers {@code ada}.
 */
@MicronautTest
class LoginFlowTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Test
    void successfulLoginReturnsSessionToken() {
        HttpResponse<String> response = client.toBlocking().exchange(
                HttpRequest.POST("/login", new LoginRequest("ada", "correct-horse-battery-staple")),
                String.class);

        assertEquals(HttpStatus.OK, response.getStatus());
        assertTrue(response.body().contains("sessionToken"), "missing sessionToken in response body");
    }

    @Test
    void unknownUserReturns401() {
        HttpClientResponseException thrown = assertThrows(
                HttpClientResponseException.class,
                () -> client.toBlocking().exchange(
                        HttpRequest.POST("/login", new LoginRequest("nobody", "whatever")),
                        String.class));

        assertEquals(HttpStatus.UNAUTHORIZED, thrown.getStatus());
    }
}
