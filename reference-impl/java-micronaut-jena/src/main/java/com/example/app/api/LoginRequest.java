package com.example.app.api;

/** Login request DTO. Lives on the HTTP boundary only. */
public record LoginRequest(String username, String password) {}
