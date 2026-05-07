package com.example.app.api;

/** Login response DTO. Lives on the HTTP boundary only. */
public record LoginResponse(String sessionToken, String outcome) {}
