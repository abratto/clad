package com.example.app.infrastructure;

import dev.legible.engine.SyncEngine;
import io.micronaut.context.annotation.Requires;
import io.micronaut.core.annotation.Nullable;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.exceptions.HttpStatusException;
import jakarta.inject.Inject;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Developer-mode WYSIWID introspection endpoints over the fire-after-commit
 * engine's {@code DebugApi}: archived/in-flight flow logs, stuck actions,
 * per-concept region contents, and the registered sync rules.
 *
 * <p>Not part of the business HTTP surface: these routes inspect engine state
 * and are disabled in the {@code prod} environment.
 */
@Controller("/api/dev")
@Requires(notEnv = "prod")
public final class DebugController {

    private final SyncEngine engine;

    @Inject
    public DebugController(SyncEngine engine) {
        this.engine = engine;
    }

    /** In-flight flows (ids currently live in the engine's action log). */
    @Get(uri = "/flows", produces = io.micronaut.http.MediaType.APPLICATION_JSON)
    public List<Map<String, Object>> flows() {
        List<Map<String, Object>> out = new ArrayList<>();
        List<String> ids = new ArrayList<>(engine.inFlight().keySet());
        Collections.reverse(ids); // most recent first
        for (String id : ids) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("flowId", id);
            row.put("actionCount", engine.inFlight().get(id).invocations(id).size());
            out.add(row);
        }
        return out;
    }

    /** One flow's full attributed action chain (in-flight or archive buffer). */
    @Get(uri = "/flow/{flowId}", produces = io.micronaut.http.MediaType.APPLICATION_JSON)
    public Map<String, Object> flow(String flowId) {
        Map<String, Object> result = engine.debug().flow(flowId);
        if ("none".equals(result.get("source"))) {
            throw new HttpStatusException(HttpStatus.NOT_FOUND, "flow not found: " + flowId);
        }
        return result;
    }

    @Get(uri = "/stuck", produces = io.micronaut.http.MediaType.APPLICATION_JSON)
    public Map<String, Object> stuck() {
        return engine.debug().stuck();
    }

    @Get(uri = "/concept/{name}/facts", produces = io.micronaut.http.MediaType.APPLICATION_JSON)
    public Map<String, Object> concept(String name) {
        return engine.debug().concept(name);
    }

    @Get(uri = "/syncs", produces = io.micronaut.http.MediaType.APPLICATION_JSON)
    public List<Map<String, Object>> syncs() {
        return engine.debug().syncs();
    }
}
