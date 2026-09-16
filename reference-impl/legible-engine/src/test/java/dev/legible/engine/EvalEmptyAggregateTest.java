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
