package com.example.app.engine;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * A flow token: a small, addressable record of one action having
 * happened. See {@code methodology/architecture/FLOW_TOKENS.md}.
 *
 * <p>Tokens form a tree via {@link #parentId()}; the root token of
 * any flow is a {@code Web.handle} token whose parent is {@code null}.
 */
public record FlowToken(
        UUID id,
        UUID parentId,
        String actor,
        Instant when,
        String action,
        Map<String, Object> fields) {
}
