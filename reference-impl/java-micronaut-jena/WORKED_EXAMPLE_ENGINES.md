# Worked example — same flow, both engines

This file walks the same 3-concept chain (Origin → Middle → Terminal → Respond)
through both engines, highlighting the behavioral difference that makes the
predicate engine match the WYSIWID paper's formal semantics.

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

## Reference engine — sequential dispatch

```
1. FlowManager.rootAction("chain", {})   → writes Web/handle invocation
2. Web concept polls                      → processes request
3. Web concept completes                  → writes [routed]
4. SyncDispatcher polls                  → finds Web/handle[routed]
5. SyncDispatcher fires sync 0           → writes Origin/generate invocation
6. Origin concept polls                   → processes generate
   Origin concept writes [OK]            → actionLog.update(...) commits
                                          ← INDEPENDENT COMMIT
7. SyncDispatcher polls                   → finds Origin/generate[OK]
                                          ← 50ms gap between steps 6 and 7
8. SyncDispatcher fires sync 1           → writes Middle/transform invocation
9. Middle concept polls                   → processes transform
   Middle concept writes [DONE]          → actionLog.update(...) commits
                                          ← INDEPENDENT COMMIT
10. ... (same pattern for Terminal and Web/respond)
11. SyncDispatcher.awaitResponse()       → response found
12. SyncDispatcher.archiveFlow()         → flow archived
```

**Key behavior**: Each `writeCompletion()` commits independently before the
dispatcher notices the completion. There's a window (one poll interval, ~50ms)
between step 6 and step 7 where Origin's [OK] exists but Middle's invocation
hasn't been created yet. If a crash occurs during this window, the flow is
partially committed with no downstream invocation.

If Origin wrote [UNKNOWN] instead of [OK], the reference engine silently
commits it — no sync matches, but the outcome persists in the action log.
The flow chain simply stops.

## Predicate engine — pre-commit evaluation

```
1. FlowManager.rootAction("chain", {})   → writes Web/handle invocation
2. Web concept polls                      → processes request
3. Web concept wants to write [routed]    → PredicateConceptAgent.writeCompletion()
4. PredicateSyncDispatcher.evaluateSyncs()→ which syncs match [routed]?
5. Matched: sync 0 (Web/handle → Origin/generate)
6. batch:
   ┌─ actionLog.beginBatch()
   │─  writeCompletionSparql(...)          → writes [routed]
   │─  sync0.execute()                     → writes Origin/generate invocation
   └─ actionLog.flushBatch()              ← SINGLE TRANSACTION COMMIT
7. Origin concept polls                    → processes generate
8. Origin wants to write [OK]             → PredicateConceptAgent.writeCompletion()
9. PredicateSyncDispatcher.evaluateSyncs()→ which syncs match [OK]?
10. Matched: sync 1 (Origin/generate[OK] → Middle/transform)
11. batch:
    ┌─ actionLog.beginBatch()
    │─  writeCompletionSparql(...)          → writes [OK]
    │─  sync1.execute()                     → writes Middle/transform invocation
    └─ actionLog.flushBatch()              ← SINGLE TRANSACTION COMMIT
12. ... (same pattern for Middle → Terminal → Web/respond)
13. After Web/respond commit               → actionLog.archiveFlow()
```

**Key behavior**: Steps 8-11 happen atomically. A reader never sees Origin's
[OK] without Middle's invocation — `beginBatch()`/`flushBatch()` commits both
in one Jena transaction. No poll-interval window.

If Origin tries to write [UNKNOWN] instead of [OK]:
1. `evaluateSyncs()` returns empty list — no sync matches [UNKNOWN]
2. `SyncEvaluationException` is thrown BEFORE any SPARQL is executed
3. Origin's state is never modified. The [UNKNOWN] outcome is impossible.

## Behavioral differences at a glance

| Scenario | Reference engine | Predicate engine |
|---|---|---|
| Origin writes [OK] | Commits OK, then dispatcher fires sync 1 (50ms gap) | Commits OK + Middle invocation in one tx (atomic) |
| Origin writes [UNKNOWN] | Silently commits UNKNOWN — flow stops with no error | Throws SyncEvaluationException — state unchanged |
| Middle writes [DONE] | Same as above — dispatcher fires sync 2 | Same as above — batch fires sync 2 |
| Any step's batch fails | Irrecoverable — partial state committed | Entire composite transition rolls back |
| Web/respond [200] | Dispatcher finds it, calls archiveFlow() | PredicateConceptAgent calls archiveFlow() after batch |

## Code: Concept extending each engine

**Reference engine:**
```java
public class OriginConcept extends ConceptAgent {
    @Inject
    public OriginConcept(ActionLog log, CompletionBus bus) {
        super(log, bus);
    }

    @Override protected void processInvocation(ActionRecord inv) {
        // Do work...
        writeCompletion(inv, Map.of("outcome",
            ResourceFactory.createStringLiteral("OK"),
            "value", ResourceFactory.createStringLiteral("processed")));
        // Outcome committed. Dispatcher will notice later.
    }
}
```

**Predicate engine:**
```java
public class OriginConcept extends PredicateConceptAgent {
    @Inject
    public OriginConcept(ActionLog log, CompletionBus bus,
                         PredicateSyncDispatcher dispatcher) {
        super(log, bus, dispatcher);
    }

    @Override protected void processInvocation(ActionRecord inv) {
        // Do work...
        writeCompletion(inv, Map.of("outcome",
            ResourceFactory.createStringLiteral("OK"),
            "value", ResourceFactory.createStringLiteral("processed")));
        // PredicateSyncDispatcher evaluated syncs BEFORE the write.
        // If no sync matched [OK], SyncEvaluationException is thrown here.
        // If sync matched, completion + invocation committed atomically.
    }
}
```

The `processInvocation()` body is identical. The difference is in the base
class and what happens inside `writeCompletion()`.

### Testing concepts with the predicate engine

To test a predicate-engine concept in isolation (without registering all
syncs that fire on its outcomes), use the test-mode constructor:

```java
class OriginConceptTest extends ConceptTestBase {
    private OriginConcept concept;

    @BeforeEach
    void setUp() {
        concept = new OriginConcept(log, bus);  // test-mode — no dispatcher
    }

    @Test
    void shouldReturnOk() {
        // writes [OK] — predicate evaluation skipped in test mode
        concept.writeCompletion(inv, Map.of("outcome", ...));
        assertEquals("OK", readOutcome());
    }
}
```

The 2-arg constructor bypasses predicate evaluation so isolated concept
tests don't need syncs registered. Use the 3-arg constructor for
integration tests that verify predicate behavior (see
`PredicateEngineTest.java`).
