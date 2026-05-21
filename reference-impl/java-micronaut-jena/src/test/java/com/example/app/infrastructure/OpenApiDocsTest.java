package com.example.app.infrastructure;

import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

@MicronautTest
class OpenApiDocsTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Test
    void generated_openapi_yaml_is_exposed() {
        HttpResponse<String> response = client.toBlocking().exchange(
                HttpRequest.GET("/swagger/clad-java-reference-api-0.1.0.yml"),
                String.class);

        String body = response.body();
        assertTrue(body != null && body.contains("/login"), "OpenAPI yaml should describe /login");
        assertTrue(body != null && body.contains("LoginRequest"), "OpenAPI yaml should include LoginRequest schema");
    }

    @Test
    void swagger_ui_is_exposed() {
        HttpResponse<String> response = client.toBlocking().exchange(
                HttpRequest.GET("/swagger-ui/index.html"),
                String.class);

        String body = response.body();
        assertTrue(body != null && body.contains("id='swagger-ui'"), "Swagger UI page should render the Swagger UI container");
        assertTrue(body != null && body.contains("clad-java-reference-api-0.1.0.yml"), "Swagger UI should point at the generated spec");
    }
}