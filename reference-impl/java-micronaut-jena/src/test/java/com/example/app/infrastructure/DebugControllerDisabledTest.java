package com.example.app.infrastructure;

import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

@MicronautTest
class DebugControllerDisabledTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Test
    void debug_endpoints_are_disabled_by_default() {
        HttpClientResponseException error = org.junit.jupiter.api.Assertions.assertThrows(
                HttpClientResponseException.class,
                () -> client.toBlocking().retrieve(HttpRequest.GET("/api/dev/flows")));

        assertEquals(HttpStatus.NOT_FOUND, error.getStatus());
    }
}