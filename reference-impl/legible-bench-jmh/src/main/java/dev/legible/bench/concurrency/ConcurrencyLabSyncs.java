package dev.legible.bench.concurrency;

import dev.legible.engine.SyncRule;
import dev.legible.example.login.WebConcept;

import java.util.List;
import java.util.Map;

import static dev.legible.engine.Dsl.args;
import static dev.legible.engine.Dsl.bind;
import static dev.legible.engine.Dsl.conj;
import static dev.legible.engine.Dsl.invoke;
import static dev.legible.engine.Dsl.lit;
import static dev.legible.engine.Dsl.ref;
import static dev.legible.engine.Dsl.rule;
import static dev.legible.engine.Dsl.triggerField;
import static dev.legible.engine.Dsl.triggerInput;

/** Minimal bootstrap → concept → respond syncs for the concurrency lab. */
public final class ConcurrencyLabSyncs {

    private static final String WEB = WebConcept.NAME;
    private static final String REQUEST = WebConcept.REQUEST;
    private static final String RESPOND = WebConcept.RESPOND;
    private static final String COUNTER = CounterConcept.NAME;
    private static final String INCREMENT = CounterConcept.INCREMENT;
    private static final String ACCOUNT = AccountConcept.NAME;
    private static final String CREDIT = AccountConcept.CREDIT;
    private static final String TRANSFER = AccountConcept.TRANSFER;

    private ConcurrencyLabSyncs() {
    }

    public static List<SyncRule> all() {
        return List.of(
                incrementWhenRequestRouted(),
                respondWhenCounterIncremented(),
                creditWhenRequestRouted(),
                respondWhenAccountCredited(),
                transferWhenRequestRouted(),
                respondWhenAccountTransferred(),
                respondWhenAccountTransferRefused());
    }

    private static SyncRule incrementWhenRequestRouted() {
        return rule("IncrementWhenRequestRouted")
                .when(WEB, REQUEST, "routed")
                .matching(Map.of("route", "increment"))
                .where(bind("?counter", triggerInput("counterId")))
                .then(invoke(COUNTER, INCREMENT, args("counterId", ref("?counter"))))
                .build();
    }

    private static SyncRule respondWhenCounterIncremented() {
        return rule("RespondWhenCounterIncremented")
                .when(conj("trigger", COUNTER, INCREMENT, "INCREMENTED"))
                .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "increment")))
                .where(bind("?count", triggerField("count")))
                .then(invoke(WEB, RESPOND, args("status", lit(200), "count", ref("?count"))))
                .build();
    }

    private static SyncRule creditWhenRequestRouted() {
        return rule("CreditWhenRequestRouted")
                .when(WEB, REQUEST, "routed")
                .matching(Map.of("route", "credit"))
                .where(bind("?account", triggerInput("accountId")),
                        bind("?amount", triggerInput("amount")))
                .then(invoke(ACCOUNT, CREDIT,
                        args("accountId", ref("?account"), "amount", ref("?amount"))))
                .build();
    }

    private static SyncRule respondWhenAccountCredited() {
        return rule("RespondWhenAccountCredited")
                .when(conj("trigger", ACCOUNT, CREDIT, "CREDITED"))
                .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "credit")))
                .where(bind("?balance", triggerField("balance")))
                .then(invoke(WEB, RESPOND, args("status", lit(200), "balance", ref("?balance"))))
                .build();
    }

    private static SyncRule transferWhenRequestRouted() {
        return rule("TransferWhenRequestRouted")
                .when(WEB, REQUEST, "routed")
                .matching(Map.of("route", "transfer"))
                .where(bind("?from", triggerInput("from")),
                        bind("?to", triggerInput("to")),
                        bind("?amount", triggerInput("amount")))
                .then(invoke(ACCOUNT, TRANSFER,
                        args("from", ref("?from"), "to", ref("?to"), "amount", ref("?amount"))))
                .build();
    }

    private static SyncRule respondWhenAccountTransferred() {
        return rule("RespondWhenAccountTransferred")
                .when(conj("trigger", ACCOUNT, TRANSFER, "TRANSFERRED"))
                .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "transfer")))
                .then(invoke(WEB, RESPOND, args("status", lit(200))))
                .build();
    }

    private static SyncRule respondWhenAccountTransferRefused() {
        return rule("RespondWhenAccountTransferRefused")
                .when(conj("trigger", ACCOUNT, TRANSFER, "refused"))
                .and(conj("requested", WEB, REQUEST, "routed").matching(Map.of("route", "transfer")))
                .then(invoke(WEB, RESPOND, args("status", lit(409), "reason", lit("insufficient"))))
                .build();
    }
}
