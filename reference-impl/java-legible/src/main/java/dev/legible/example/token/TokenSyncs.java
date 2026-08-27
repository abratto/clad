package dev.legible.example.token;

import dev.legible.engine.Clause;
import dev.legible.engine.Source;
import dev.legible.engine.SyncRule;
import dev.legible.engine.ThenInvocation;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static dev.legible.engine.SyncRule.invoke;
import static dev.legible.engine.SyncRule.lit;
import static dev.legible.engine.SyncRule.ref;

/**
 * The one construct the earlier examples never exercised: {@code bind(uuid())}
 * in a sync's {@code where} clause. The token id is minted by the sync
 * ({@code bind(uuid() as ?tokenId)}) and handed to {@code Token.issue}, which
 * records it without minting its own id.
 */
public final class TokenSyncs {

    private TokenSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(requestToIssue(), issueToRespond());
    }

    private static SyncRule requestToIssue() {
        return SyncRule.of(
                "WhenWebRequestRoutedThenTokenIssueForIssue",
                "Web", "request", "routed",
                List.of(
                        new Clause.Bind("?route", new Source.TriggerInput("route")),
                        new Clause.Guard("?route", lit("issue")),
                        new Clause.Bind("?userId", new Source.TriggerInput("userId")),
                        new Clause.Bind("?tokenId", new Source.Uuid())),
                List.of(invoke("Token", "issue",
                        Map.of("tokenId", ref("?tokenId"), "userId", ref("?userId")))));
    }

    private static SyncRule issueToRespond() {
        return SyncRule.of(
                "WhenTokenIssueIssuedThenWebRespondForIssue",
                "Token", "issue", "ISSUED",
                List.of(new Clause.Bind("?tokenId", new Source.TriggerField("tokenId"))),
                List.of(respond(Map.of("tokenId", ref("?tokenId")))));
    }

    private static ThenInvocation respond(Map<String, Source> fields) {
        Map<String, Source> args = new LinkedHashMap<>();
        args.put("status", lit(200));
        args.putAll(fields);
        return invoke("Web", "respond", args);
    }
}
