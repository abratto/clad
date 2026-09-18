package com.example.app.syncs;

import dev.legible.engine.Clause;
import dev.legible.engine.Source;
import dev.legible.engine.SyncRule;
import java.util.List;
import java.util.Map;
import static dev.legible.engine.SyncRule.invoke;
import static dev.legible.engine.SyncRule.lit;
import static dev.legible.engine.SyncRule.ref;

/**
 * Row 1-to-2: when Web/request[routed] then UserNaming.lookupByUsername(username).
 *
 * <p>The declarative SyncRule realization of the Stage 03 LookupByUsernameForLoginWhenRequestRouted.sync.md (grammar v2 name: LookupByUsernameForLoginWhenRequestRouted; see maintenance/sync-dsl-legibility.md).
 * Trigger and target tokens are copied verbatim from the approved chain
 * table (literal lock). No imperative branching, no state, no I/O (R3).
 */
public final class LookupByUsernameForLoginWhenRequestRouted {

    public SyncRule rule() {
        return SyncRule.of(
                // renamed to grammar v2: "LookupByUsernameForLoginWhenRequestRouted" -> "LookupByUsernameForLoginWhenRequestRouted"
                "LookupByUsernameForLoginWhenRequestRouted",
                "Web", "request", "routed",
                List.of(new Clause.Bind("?u", new Source.TriggerInput("username"))),
                List.of(invoke("UserNaming", "lookupByUsername", Map.of("username", ref("?u")))));
    }
}
