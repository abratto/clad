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
 * Row 3b[BAD_PASSWORD]-to-4b: respond 401 opaque.
 *
 * <p>The declarative SyncRule realization of the Stage 03 WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.sync.md (grammar v2 name: WebRespondForLoginWhenPasswordAuthCheckBadPassword; see maintenance/sync-dsl-legibility.md).
 * Trigger and target tokens are copied verbatim from the approved chain
 * table (literal lock). No imperative branching, no state, no I/O (R3).
 */
public final class WebRespondForLoginWhenPasswordAuthCheckBadPassword {

    public SyncRule rule() {
        return SyncRule.of(
                // renamed to grammar v2: "WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin" -> "WebRespondForLoginWhenPasswordAuthCheckBadPassword"
                "WebRespondForLoginWhenPasswordAuthCheckBadPassword",
                "PasswordAuth", "check", "BAD_PASSWORD",
                List.of(),
                List.of(invoke("Web", "respond", Map.of(
                        "status", lit(401),
                        "message", lit("username or password didn't match")))));
    }
}
