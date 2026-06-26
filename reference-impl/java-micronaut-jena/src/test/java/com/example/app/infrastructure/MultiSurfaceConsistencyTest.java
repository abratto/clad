package com.example.app.infrastructure;

import com.example.app.api.LoginRequest;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.MediaType;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Proves that REST and GraphQL surfaces produce identical flow behaviour
 * for the same login inputs. Same CLAD engine, same flow tokens, different
 * transport encodings.
 */
@MicronautTest
class MultiSurfaceConsistencyTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Test
    void restLoginReturns200ForValidCredentials() {
        var req = HttpRequest.POST("/api/login",
                new LoginRequest("ada", "correct-horse-battery-staple"))
                .contentType(MediaType.APPLICATION_JSON);
        HttpResponse<String> resp = client.toBlocking().exchange(req, String.class);

        assertEquals(HttpStatus.OK, resp.getStatus());
        assertNotNull(resp.getHeaders().get("X-Flow-Token"));
        assertTrue(resp.body().contains("sessionToken"));
    }

    @Test
    void restLoginReturns401ForWrongPassword() {
        try {
            var req = HttpRequest.POST("/api/login",
                    new LoginRequest("ada", "wrong"))
                    .contentType(MediaType.APPLICATION_JSON);
            client.toBlocking().exchange(req, String.class);
            fail("Expected 401");
        } catch (io.micronaut.http.client.exceptions.HttpClientResponseException e) {
            assertEquals(HttpStatus.UNAUTHORIZED, e.getStatus());
            assertTrue(e.getResponse().getBody(String.class).orElse("")
                    .contains("username or password"));
        }
    }

    @Test
    void graphqlLoginReturns200ForValidCredentials() {
        String query = "mutation { login(loginRequestInput: { username: \"ada\", password: \"correct-horse-battery-staple\" }) { sessionToken } }";
        var req = HttpRequest.POST("/graphql", Map.of("query", query))
                .contentType(MediaType.APPLICATION_JSON);
        HttpResponse<String> resp = client.toBlocking().exchange(req, String.class);

        assertEquals(HttpStatus.OK, resp.getStatus());
        assertTrue(resp.body().contains("sessionToken"));
        assertFalse(resp.body().contains("errors"));
        assertNotNull(resp.getHeaders().get("X-Flow-Token"),
                "GraphQL should emit X-Flow-Token header");
    }

    @Test
    void graphqlStatusEndpointReturnsInitialized() {
        var req = HttpRequest.GET("/graphql/status");
        HttpResponse<Map> resp = client.toBlocking().exchange(req, Map.class);
        assertEquals(HttpStatus.OK, resp.getStatus());
        assertTrue((Boolean) resp.body().get("initialized"), "GraphQL should be initialized");
    }

    @Test
    void legacyLoginAndRestLoginBothReturn200() {
        var body = new LoginRequest("ada", "correct-horse-battery-staple");
        var restReq = HttpRequest.POST("/api/login", body).contentType(MediaType.APPLICATION_JSON);
        HttpResponse<String> restResp = client.toBlocking().exchange(restReq, String.class);

        var legacyReq = HttpRequest.POST("/login", body).contentType(MediaType.APPLICATION_JSON);
        HttpResponse<String> legacyResp = client.toBlocking().exchange(legacyReq, String.class);

        assertEquals(HttpStatus.OK, restResp.getStatus());
        assertEquals(HttpStatus.OK, legacyResp.getStatus());
        assertTrue(restResp.body().contains("sessionToken"), "REST should return sessionToken");
    }
}
