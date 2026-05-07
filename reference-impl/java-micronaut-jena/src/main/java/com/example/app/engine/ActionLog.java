package com.example.app.engine;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * In-memory append-only log of {@link FlowToken}s.
 *
 * <p>An RDF-backed implementation will replace this in a follow-up
 * iteration; the contract (append + read-all) stays the same.
 */
public final class ActionLog {

    private final List<FlowToken> tokens = new ArrayList<>();

    public synchronized void append(FlowToken token) {
        tokens.add(token);
    }

    public synchronized List<FlowToken> all() {
        return Collections.unmodifiableList(new ArrayList<>(tokens));
    }
}
