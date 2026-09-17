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
 * Row 3b[LOCKED]-to-4c: respond 401 with the visible lockout message.
 *
 * <p>The declarative SyncRule realization of the Stage 03 RespondWhenCheckLocked.sync.md (grammar v2 name: RespondWhenCheckLocked; see maintenance/sync-dsl-legibility.md).
 * Trigger and target tokens are copied verbatim from the approved chain
 * table (literal lock). No imperative branching, no state, no I/O (R3).
 */
public final class RespondWhenCheckLocked {

    public SyncRule rule() {
        return SyncRule.of(
                // renamed to grammar v2: "RespondWhenCheckLocked" -> "RespondWhenCheckLocked"
                "RespondWhenCheckLocked",
                "PasswordAuth", "check", "LOCKED",
                List.of(),
                List.of(invoke("Web", "respond", Map.of(
                        "status", lit(401),
                        "message", lit("Too many attempts. Try again in 15 minutes.")))));
    }
}
