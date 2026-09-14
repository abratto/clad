package dev.legible.example.token;

import dev.legible.engine.SyncRule;

import java.util.List;
import java.util.Map;

import static dev.legible.engine.Dsl.args;
import static dev.legible.engine.Dsl.bind;
import static dev.legible.engine.Dsl.invoke;
import static dev.legible.engine.Dsl.lit;
import static dev.legible.engine.Dsl.ref;
import static dev.legible.engine.Dsl.rule;
import static dev.legible.engine.Dsl.triggerField;
import static dev.legible.engine.Dsl.triggerInput;
import static dev.legible.engine.Dsl.uuid;
import static dev.legible.example.token.TokenConcept.ISSUE;
import static dev.legible.example.token.TokenConcept.NAME;

/**
 * The one construct the earlier examples never exercised: {@code bind(uuid())}
 * in a sync's {@code where} clause. The token id is minted by the sync
 * ({@code bind(uuid() as ?tokenId)}) and handed to {@code Token.issue}, which
 * records it without minting its own id.
 *
 * <p>Names follow the effect-first grammar (see
 * {@code maintenance/sync-dsl-legibility.md}):
 * {@code <TargetConcept><TargetAction>[For<Scope>]When<TriggerConcept><TriggerAction><TriggerCompletion>}.
 * Route discrimination is a {@code when}-matcher
 * ({@code Web/respond: [ route: "issue" ]} on the trigger token), not a
 * {@code where} clause.
 */
public final class TokenSyncs {

    private TokenSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(tokenIssueForIssue(), webRespondForIssueWhenTokenIssueIssued());
    }

    private static SyncRule tokenIssueForIssue() {
        return rule("TokenIssueForIssueWhenWebRequestRouted")
            .when("Web", "request", "routed")
            .matching(Map.of("route", "issue"))
            .where(bind("?userId", triggerInput("userId")),
                   bind("?tokenId", uuid()))
            .then(invoke(NAME, ISSUE,
                    args("tokenId", ref("?tokenId"), "userId", ref("?userId"))))
            .build();
    }

    private static SyncRule webRespondForIssueWhenTokenIssueIssued() {
        return rule("WebRespondForIssueWhenTokenIssueIssued")
            .when(NAME, ISSUE, "ISSUED")
            .where(bind("?tokenId", triggerField("tokenId")))
            .then(invoke("Web", "respond",
                    args("status", lit(200), "tokenId", ref("?tokenId"))))
            .build();
    }
}
