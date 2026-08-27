package com.example.app;

import dev.clad.engine.ActionLog;
import dev.clad.engine.CompletionBus;
import dev.clad.engine.FlowManager;
import org.junit.jupiter.api.BeforeEach;

/** Shared test fixtures for concept-level tests. */
public abstract class ConceptTestBase {

    protected ActionLog log;
    protected CompletionBus bus;
    protected FlowManager flow;

    @BeforeEach
    void setUpEngine() {
        log = new ActionLog();
        bus = new CompletionBus();
        flow = new FlowManager(log, bus);
    }
}
