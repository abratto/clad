# Worked example — the transactional engine

This file walks a 3-concept chain (Origin → Middle → Terminal → Respond)
through the engine, showing how pre-commit sync evaluation matches the
WYSIWID paper's formal synchronization semantics.

**Context:** All concepts in these examples share one JVM and one Jena Dataset.
WYSIWID concepts are modular code boundaries, not network boundaries — see the
[modular monolith section in the README](README.md#architecture-a-modular-monolith).

## The scenario

Three concepts and three syncs, forming a chain:

```
Origin/generate [OK]  →  Middle/transform [DONE]  →  Terminal/collect [GOT]  →  Web/respond [200]
     (sync 1)                 (sync 2)                    (sync 3)
```

Each concept processes an invocation, writes a completion with a specific
outcome, and the matching sync fires the next concept in the chain.

## Pre-commit evaluation

```
1. FlowManager.rootAction("chain", {})   → writes Web/handle invocation
2. Web concept wants to write [routed]    → ConceptAgent.writeCompletion()
3. SyncEvaluator.evaluateSyncs()          → which syncs match [routed]?
4. Matched: sync 0 (Web/handle → Origin/generate)
5. batch:
   ┌─ actionLog.beginBatch()
   │─  writeCompletionSparql(...)          → writes [routed]
   │─  sync0.execute()                     → writes Origin/generate invocation
   └─ actionLog.flushBatch()              ← SINGLE TRANSACTION COMMIT
6. Origin concept polls                    → processes generate
7. Origin wants to write [OK]             → ConceptAgent.writeCompletion()
8. SyncEvaluator.evaluateSyncs()          → which syncs match [OK]?
9. Matched: sync 1 (Origin/generate[OK] → Middle/transform)
10. batch:
    ┌─ actionLog.beginBatch()
    │─  writeCompletionSparql(...)          → writes [OK]
    │─  sync1.execute()                     → writes Middle/transform invocation
    └─ actionLog.flushBatch()              ← SINGLE TRANSACTION COMMIT
11. ... (same pattern for Middle → Terminal → Web/respond)
12. After Web/respond commit               → actionLog.archiveFlow()
```

**Key behavior**: Steps 7-10 happen atomically. A reader never sees Origin's
[OK] without Middle's invocation — `beginBatch()`/`flushBatch()` commits both
in one Jena transaction. There is no poll-interval window of inconsistency.

If Origin tries to write [UNKNOWN] instead of [OK]:
1. `evaluateSyncs()` returns empty — no sync matches [UNKNOWN]
2. `SyncEvaluationException` is thrown BEFORE any SPARQL is executed
3. Origin's state is never modified. The [UNKNOWN] outcome is impossible.

## Code

```java
public class OriginConcept extends ConceptAgent {
    @Inject
    public OriginConcept(ActionLog log, CompletionBus bus,
                         SyncEvaluator evaluator) {
        super(log, bus, evaluator);
    }

    @Override protected void processInvocation(ActionRecord inv) {
        // Do work...
        writeCompletion(inv, Map.of("outcome",
            ResourceFactory.createStringLiteral("OK"),
            "value", ResourceFactory.createStringLiteral("processed")));
        // SyncEvaluator evaluated syncs BEFORE the write.
        // If no sync matched [OK], SyncEvaluationException is thrown here.
        // If sync matched, completion + invocation committed atomically.
    }
}
```

### Testing concepts in isolation

To test a concept in isolation (without registering all syncs that fire on
its outcomes), use the test-mode constructor:

```java
class OriginConceptTest extends ConceptTestBase {
    private OriginConcept concept;

    @BeforeEach
    void setUp() {
        concept = new OriginConcept(log, bus);  // test-mode — no evaluator
    }

    @Test
    void shouldReturnOk() {
        // writes [OK] — sync evaluation skipped in test mode
        concept.writeCompletion(inv, Map.of("outcome", ...));
        assertEquals("OK", readOutcome());
    }
}
```

The 2-arg constructor bypasses sync evaluation so isolated concept tests don't
need syncs registered. Use the 3-arg constructor for integration tests that
verify sync evaluation (see `ConceptAgentTest.java`).
