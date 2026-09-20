package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The negative state pattern ({@code absent}, maintenance/
 * engine-absent-state-guard.md): keep a frame only if a subject has no value —
 * optionally, no value equal to a given one — for a predicate.
 *
 * <p>Motivating case (UC-04-return-copy): "the member's <em>remaining open</em>
 * loans" is every loan whose {@code borrower} is the member and which has no
 * {@code returnedAt}. Every source the DSL had enumerates state; none could
 * express an absence, and {@code collect} takes no filter.
 */
class AbsentClauseTest {

    private final FactStore facts = new InMemoryFactStore();
    private final ActionLog log = new InMemoryActionLog();
    private final WhereEvaluator ev = new WhereEvaluator(facts, log);

    private static final Invocation INV =
            new Invocation("t1", "f1", null, null, "Lending", "close",
                    Map.of("memberId", "m1"), 0L);
    private static final Completion COMP =
            new Completion("t1", "f1", "Lending", "close", "Returned",
                    Map.of("memberId", "m1"), 0L);

    private List<Map<String, Object>> eval(Clause... where) {
        return ev.evaluate(SyncRule.of("r", "Lending", "close", "Returned",
                List.of(where), List.of()), INV, COMP);
    }

    /** A loan held by {@code memberId}; {@code returnedAt} null means still open. */
    private void loan(String loanId, String memberId, String returnedAt) {
        Region lending = facts.region("Lending");
        lending.write(loanId, "borrower", memberId);
        if (returnedAt != null) {
            lending.write(loanId, "returnedAt", returnedAt);
        }
    }

    private Clause membersLoans() {
        return Dsl.fanOut("?loanId", "Lending", "borrower", Dsl.lit("m1"));
    }

    @Test
    void shouldKeepTheFrameWhenThePropertyIsAbsent() {
        loan("l1", "m1", null);

        List<Map<String, Object>> out = eval(
                membersLoans(),
                Dsl.absent("?loanId", "Lending", "returnedAt"));

        assertEquals(1, out.size(), "an open loan has no returnedAt");
        assertEquals("l1", out.get(0).get("?loanId"));
    }

    @Test
    void shouldDropTheFrameWhenThePropertyIsPresent() {
        loan("l1", "m1", "r1");

        List<Map<String, Object>> out = eval(
                membersLoans(),
                Dsl.absent("?loanId", "Lending", "returnedAt"));

        assertEquals(0, out.size(), "a loan with a returnedAt is closed");
    }

    @Test
    void shouldDropOnlyWhenTheValueMatches() {
        loan("l1", "m1", "r1");

        assertEquals(1, eval(membersLoans(),
                Dsl.absent("?loanId", "Lending", "returnedAt", Dsl.lit("r2"))).size(),
                "no returnedAt equal to r2 — the frame survives");
        assertEquals(0, eval(membersLoans(),
                Dsl.absent("?loanId", "Lending", "returnedAt", Dsl.lit("r1"))).size(),
                "the returnedAt equals r1 — the frame is dropped");
    }

    @Test
    void shouldFailClosedWhenTheSubjectIsUnbound() {
        loan("l1", "m1", null);

        // No fan-out, so ?loanId is unbound: the absence cannot be checked, and
        // the clause must never assert one it could not.
        List<Map<String, Object>> out = eval(
                Dsl.absent("?loanId", "Lending", "returnedAt"));

        assertEquals(0, out.size(), "unbound subject drops the frame");
    }

    @Test
    void shouldPreserveEarlierBindings() {
        loan("l1", "m1", null);

        List<Map<String, Object>> out = eval(
                Dsl.bind("?memberId", Dsl.triggerField("memberId")),
                Dsl.fanOut("?loanId", "Lending", "borrower", Dsl.ref("?memberId")),
                Dsl.absent("?loanId", "Lending", "returnedAt"));

        assertEquals(1, out.size());
        assertEquals("m1", out.get(0).get("?memberId"));
        assertEquals("l1", out.get(0).get("?loanId"));
    }

    @Test
    void shouldCollectTheSubjectsWithoutTheProperty() {
        loan("l1", "m1", null);
        loan("l2", "m1", "r1");          // closed — must not appear
        loan("l3", "m1", null);
        loan("l4", "m2", null);          // another member's — must not appear

        List<Map<String, Object>> out = eval(
                Dsl.bind("?memberId", Dsl.triggerField("memberId")),
                Dsl.fanOut("?loanId", "Lending", "borrower", Dsl.ref("?memberId")),
                Dsl.absent("?loanId", "Lending", "returnedAt"),
                Dsl.collectBy("?openLoans", Dsl.ref("?loanId"), null));

        assertEquals(1, out.size());
        List<?> open = (List<?>) out.get(0).get("?openLoans");
        assertEquals(2, open.size(), "the member's open loans, and only those");
        assertTrue(open.contains("l1") && open.contains("l3"), open.toString());
    }

    @Test
    void shouldYieldAnEmptyListWhenEveryLoanIsClosed() {
        loan("l1", "m1", "r1");

        // collectBy is empty-safe (maintenance/engine-empty-safe-aggregate.md):
        // a zero-item collection is a value, so the response can still say
        // "you hold nothing" instead of never firing.
        List<Map<String, Object>> out = eval(
                Dsl.bind("?memberId", Dsl.triggerField("memberId")),
                Dsl.fanOut("?loanId", "Lending", "borrower", Dsl.ref("?memberId")),
                Dsl.absent("?loanId", "Lending", "returnedAt"),
                Dsl.collectBy("?openLoans", Dsl.ref("?loanId"), null));

        assertEquals(1, out.size());
        assertEquals(List.of(), out.get(0).get("?openLoans"));
    }
}
