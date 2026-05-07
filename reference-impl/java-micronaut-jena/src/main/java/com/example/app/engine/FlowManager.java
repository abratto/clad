package com.example.app.engine;

import java.time.Clock;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * The single point at which concepts emit flow tokens. Concept actions
 * call {@link #emit(String, String, java.util.UUID, java.util.Map)};
 * see hard rule R5.
 */
public final class FlowManager {

    private final ActionLog log;
    private final Clock clock;

    public FlowManager(ActionLog log) {
        this(log, Clock.systemUTC());
    }

    public FlowManager(ActionLog log, Clock clock) {
        this.log = log;
        this.clock = clock;
    }

    public FlowToken emit(String action, String actor, UUID parentId, Map<String, Object> fields) {
        FlowToken token = new FlowToken(
                UUID.randomUUID(),
                parentId,
                actor,
                Instant.now(clock),
                action,
                Map.copyOf(fields));
        log.append(token);
        return token;
    }
}
