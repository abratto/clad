package dev.legible.example.login;

import dev.legible.engine.Completion;
import dev.legible.engine.FlowRecord;
import dev.legible.engine.Invocation;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Stage 05 back-trace: the runtime flow-token chain (the ordered
 * {@code Concept/action} sequence + outcomes on the action log) must match the
 * chain table, and every non-root action must carry the sync that authorized it
 * ({@code causedBySync}). This is the runtime half of the contract loop — the
 * spec half ({@code verify_action_chain.py}) is engine-agnostic and unchanged.
 */
class FlowTraceTest {

    private LoginApp app;

    // Chain-table predictions from 01b (login-all-scenarios-chain.md). The
    // spec writes Web/handle and NOT_FOUND; the runtime names are Web/request
    // and refused (the reconciliation the formal pass will land in the specs).
    private static final List<String> SUCCESS_CHAIN =
            List.of("Web/request", "UserNaming/lookupByUsername", "PasswordAuth/check", "Session/grant", "Web/respond");
    private static final List<String> WRONG_PASSWORD_CHAIN =
            List.of("Web/request", "UserNaming/lookupByUsername", "PasswordAuth/check", "Web/respond");
    private static final List<String> UNKNOWN_USER_CHAIN =
            List.of("Web/request", "UserNaming/lookupByUsername", "Web/respond");
    private static final List<String> LOCKOUT_CHAIN =
            List.of("Web/request", "UserNaming/lookupByUsername", "PasswordAuth/check", "Web/respond");

    private static final List<String> SUCCESS_OUTCOMES = List.of("routed", "FOUND", "OK", "GRANTED", "sent");
    private static final List<String> WRONG_PASSWORD_OUTCOMES = List.of("routed", "FOUND", "BAD_PASSWORD", "sent");
    private static final List<String> UNKNOWN_USER_OUTCOMES = List.of("routed", "refused", "sent");
    private static final List<String> LOCKOUT_OUTCOMES = List.of("routed", "FOUND", "LOCKED", "sent");

    @BeforeEach
    void setUp() {
        app = LoginApp.create();
    }

    @Test
    void successfulLoginRuntimeChainMatchesChainTable() {
        app.seedUser("alice", "secret");
        app.login("alice", "secret");
        assertTrace(SUCCESS_CHAIN, SUCCESS_OUTCOMES);
    }

    @Test
    void wrongPasswordRuntimeChainMatchesChainTable() {
        app.seedUser("alice", "secret");
        app.login("alice", "wrong");
        assertTrace(WRONG_PASSWORD_CHAIN, WRONG_PASSWORD_OUTCOMES);
    }

    @Test
    void unknownUserRuntimeChainMatchesChainTable() {
        app.seedUser("alice", "secret");
        app.login("nobody", "whatever");
        assertTrace(UNKNOWN_USER_CHAIN, UNKNOWN_USER_OUTCOMES);
    }

    @Test
    void lockoutRuntimeChainMatchesChainTable() {
        app.seedUser("alice", "secret");
        for (int i = 0; i < 5; i++) {
            app.login("alice", "wrong");
        }
        app.login("alice", "secret");
        assertTrace(LOCKOUT_CHAIN, LOCKOUT_OUTCOMES);
    }

    private void assertTrace(List<String> expectedChain, List<String> expectedOutcomes) {
        FlowRecord rec = app.engine().archiver().buffer().latest().orElseThrow();

        List<String> chain = rec.invocations().stream()
                .map(i -> i.concept() + "/" + i.action())
                .toList();
        assertEquals(expectedChain, chain, "runtime flow-token chain must match the chain table");

        Map<String, Completion> byId = rec.completions().stream()
                .collect(Collectors.toMap(Completion::actionId, Function.identity()));
        List<String> outcomes = rec.invocations().stream()
                .map(Invocation::actionId)
                .map(byId::get)
                .map(Completion::outcome)
                .toList();
        assertEquals(expectedOutcomes, outcomes, "runtime outcomes must match the chain table");

        // Every non-root action must back-trace to an authorizing sync.
        for (Invocation inv : rec.invocations().subList(1, rec.invocations().size())) {
            assertNotNull(inv.causedBySync(),
                    inv.concept() + "/" + inv.action() + " must be authorized by a sync");
        }
    }
}
