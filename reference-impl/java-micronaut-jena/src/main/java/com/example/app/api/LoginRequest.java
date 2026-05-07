package com.example.app.api;

import io.micronaut.core.annotation.Introspected;

/** JSON body for {@code POST /login}. */
@Introspected
public record LoginRequest(String username, String password) {}
