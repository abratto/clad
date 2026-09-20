package dev.legible.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Empty-safe frame-set aggregation (WhereEvaluator): an aggregate over ZERO
 * frames still emits one frame carrying the empty list, so an empty relation
 * does not silently drop the downstream rule (conduit rebuild UC-07).
 */
class EvalEmptyAggregateTest {

    private final FactStore facts = new InMemoryFactStore();
    private final ActionLog log = new InMemoryActionLog();
    private final WhereEvaluator ev = new WhereEvaluator(facts, log);

    private static final Invocation INV =
            new Invocation("t1", "f1", null, null, "C", "act", Map.of(), 0L);
    private static final Completion COMP =
            new Completion("t1", "f1", "C", "act", "ok", Map.of(), 0L);

    @Test
    void emptyAggregateCarriesTheBindingsFromBeforeTheFanOut() {
        // UC-04: the member's loans are fanned out, `absent returnedAt` filters
        // them all away, and the aggregate must still carry the bindings bound
        // BEFORE the fan-out — not the fan-out's own variable (the loan the
        // filter just excluded) and not a blank frame, which would hand the
        // `then` clause nulls for every earlier field.
        // The loan EXISTS — so the fan-out yields a frame and it is `absent` that
        // empties the set, not the fan-out.
        Region lending = facts.region("Lending");
        lending.write("l1", "borrower", "m1");
        lending.write("l1", "returnedAt", "2026-09-17T10:00:00Z");

        SyncRule rule = SyncRule.of("r", "C", "act", "ok",
                List.of(Dsl.bind("?memberId", Dsl.lit("m1")),
                        Dsl.fanOut("?loanId", "Lending", "borrower", Dsl.lit("m1")),
                        Dsl.absent("?loanId", "Lending", "returnedAt"),
                        Dsl.collectBy("?openLoans", Dsl.ref("?loanId"), null)),
                List.of());

        List<Map<String, Object>> frames = ev.evaluate(rule, INV, COMP);

        assertEquals(1, frames.size(), "one frame survives with an empty list");
        assertEquals(List.of(), frames.get(0).get("?openLoans"),
                "the filtered-out loan must not be collected");
        assertEquals("m1", frames.get(0).get("?memberId"),
                "a binding made before the fan-out must survive the empty aggregate");
    }

    @Test
    void collectByOverZeroFramesEmitsOneFrameWithEmptyList() {
        // No Commenting facts exist: the fan-out finds nothing.
        SyncRule rule = SyncRule.of("r", "C", "act", "ok",
                List.of(Dsl.fanOut("?commentId", "Commenting", "articleId", Dsl.lit("a1")),
                        Dsl.collectBy("?ids", Dsl.ref("?commentId"), null)),
                List.of());

        List<Map<String, Object>> frames = ev.evaluate(rule, INV, COMP);

        assertEquals(1, frames.size(), "one frame survives with an empty list");
        assertEquals(List.of(), frames.get(0).get("?ids"));
    }
}
