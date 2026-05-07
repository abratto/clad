package com.example.app;

import com.example.app.engine.ActionLog;
import com.example.app.engine.FlowManager;

/** Shared test fixtures for concept-level tests. */
public abstract class ConceptTestBase {

    protected ActionLog log;
    protected FlowManager flow;

    protected void setUpEngine() {
        log = new ActionLog();
        flow = new FlowManager(log);
    }
}
