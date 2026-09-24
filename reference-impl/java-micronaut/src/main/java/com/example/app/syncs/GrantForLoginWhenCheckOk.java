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
 * Row 3b[OK]-to-4a: when PasswordAuth.check[OK] then Session.grant(userId).
 *
 * <p>The declarative SyncRule realization of the Stage 03 GrantForLoginWhenCheckOk.sync.md (grammar v2 name: GrantForLoginWhenCheckOk; see maintenance/sync-dsl-legibility.md).
 * Trigger and target tokens are copied verbatim from the approved chain
 * table (literal lock). No imperative branching, no state, no I/O (R3).
 */
public final class GrantForLoginWhenCheckOk {

    public SyncRule rule() {
        return SyncRule.of(
                // renamed to grammar v2: "GrantForLoginWhenCheckOk" -> "GrantForLoginWhenCheckOk"
                "GrantForLoginWhenCheckOk",
                "PasswordAuth", "check", "OK",
                List.of(new Clause.Bind("?user", new Source.TriggerField("userId"))),
                List.of(invoke("Session", "grant", Map.of("userId", ref("?user")))));
    }
}
