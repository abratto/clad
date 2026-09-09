package com.example.app.engine;

import dev.legible.engine.SyncEngine;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * A transport-facing view over the engine: invoke the flow root
 * ({@code Web/request}, {@code route=login}) and return the authored
 * {@code Web/respond} fields.
 *
 * <p>This is where application code meets the engine boundary. It holds no
 * business logic — concepts and syncs do all of the domain work; the gateway
 * is the piece an HTTP adapter, CLI adapter, or test harness can share.
 */
public final class LoginGateway {

    private final SyncEngine engine;

    public LoginGateway(SyncEngine engine) {
        this.engine = engine;
    }

    /** Runs the login flow; returns the Web/respond field map (status + payload). */
    public Map<String, Object> login(String username, String password) {
        Map<String, Object> input = new LinkedHashMap<>();
        input.put("route", "login");
        input.put("username", username);
        input.put("password", password);
        return engine.run("Web", "request", input);
    }

    public SyncEngine engine() {
        return engine;
    }
}
