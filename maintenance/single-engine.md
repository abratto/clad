# Maintenance change — `single-engine`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Remove the reference (non-transactional) engine and keep only the predicate (transactional) engine.

## Why

The WYSIWID paper's core synchronization guarantee is that an action
`a_A` in Concept A and the action `a_B` it triggers in Concept B occur
*co-instantaneously* — atomically. The reference engine violates this: each
action commits independently and the dispatcher fires syncs on a later poll,
leaving a window of inconsistency (and silently dropping unmatched outcomes).

The predicate engine implements the guarantee (syncs evaluated before commit;
completion + invocations in one Jena transaction; unmatched outcomes rejected).

The two engines are not actually a clean either/or today:

- Every concrete concept already extends `PredicateConceptAgent`.
- `engine.mode=reference` only *disables* `PredicateEngineStartupCheck`; it does
  not switch behavior — concepts would still extend `PredicateConceptAgent`.
- `SyncDispatcher` (the "reference" dispatcher) is still the runtime driver
  injected by `WebController`/`AuthController`/`GraphQLController`.
- `TransactionManager` is dead code (never instantiated). `PredicateFlowManager`
  is a no-op subclass (nothing injects it).

So this change collapses the split: the predicate engine becomes the only
engine, and the misleading `engine.mode` toggle disappears.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Same `Web/respond` contract; concept completion SPARQL unchanged |
| Action ordering and sync deduplication | preserved | Sync WHERE clauses and `FILTER NOT EXISTS` dedup unchanged |
| Flow-token lineage | preserved | Flow tokens still span the action chain; archive flow unchanged |
| Storage/retention semantics | preserved | No change to SplitStorage/FlowArchiveSink in this change |
| Unmatched-outcome semantics | changed | Reference mode's "silently succeed" path is removed; unmatched non-respond outcomes always throw `SyncEvaluationException`. This is the already-default predicate behavior. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | README "reference vs predicate" section, `clad.properties` `engine.mode` removed |
| Profile configuration or deployment files | yes | `clad.properties` |
| Engine/runtime implementation | yes | `ConceptAgent` (absorbs predicate semantics), `SyncEvaluator` (new, renamed `PredicateSyncDispatcher`), `SyncEvaluationException` moves to `engine`; delete `PredicateConceptAgent`, `PredicateSyncDispatcher`, `PredicateFlowManager`, `PredicateEngineStartupCheck`, `TransactionManager` |
| Profile tests | yes | `PredicateEngineTest`, `PredicateEngineLoadTest` (drop reference-mode half), `ConceptTestBase`, concept tests, ArchUnit `r5` |
| UC artefact chain | no | No concept/sync/spec slice changes |

## Design (file-by-file)

### Merging the engines

1. **`engine/ConceptAgent.java`** — absorbs `PredicateConceptAgent`'s
   `writeCompletion` (predicate evaluation + atomic composite write) and adds a
   `SyncEvaluator evaluator` field. Two constructors: production
   `(actionLog, completionBus, evaluator)` and test `(actionLog, completionBus)`
   with `evaluator == null` (predicate check bypassed). `writeRefusal`/`writeError`
   are unchanged (they already only signal the bus; syncs fire via the dispatcher).
   `SyncEvaluationException` moves into this package.

2. **`engine/SyncEvaluator.java`** (new, renamed from `PredicateSyncDispatcher`)
   — owns `evaluateSyncs` + the `conceptIri::actionName` trigger index, injected
   by concepts. No "predicate" framing.

3. **`engine/SyncDispatcher.java`** — becomes the single dispatcher name.
   **Correction:** it is NOT possible to drop the completion-bus `runSyncAgents`
   firing — the Web bootstrap sync (`Web/request → User/lookupByUsername`) has
   no concept agent; it is fired solely by `runSyncAgents` draining the bus after
   `FlowManager.rootAction` signals. That path is shared bootstrap infrastructure,
   not "reference engine" behavior, so it is retained unchanged (dedup makes
   redundant concept-sync re-firing a no-op). Only the javadoc loses the
   "reference" framing.

4. **Delete** `predicate/PredicateConceptAgent.java`, `predicate/PredicateSyncDispatcher.java`,
   `predicate/PredicateFlowManager.java`, `predicate/PredicateEngineStartupCheck.java`,
   `predicate/TransactionManager.java`, `predicate/SyncEvaluationException.java`
   (last one moves, not deleted).

5. **`engine/predicate/` package removed entirely.**

### Concept classes

- `concepts/user/UserConcept.java`, `concepts/passwordauth/PasswordAuthConcept.java`,
  `concepts/session/SessionConcept.java` — change `extends PredicateConceptAgent`
  → `extends ConceptAgent`; constructor param `PredicateSyncDispatcher` →
  `SyncEvaluator` (production ctor only; test ctor `(log, bus)` unchanged).

### Config + docs

- **`clad.properties`** — remove `engine.mode` + its comment block.
- **README.md** — replace the "Engine mode — reference vs. predicate" section
  with a single "Engine" section describing the transactional predicate engine;
  update `Scheduler` row in the glossary table.

### Tests

- **`ConceptAgentTest`** (renamed from `PredicateEngineTest`, moved out of the
  `predicate` package) — updated `new PredicateSyncDispatcher` → `new SyncEvaluator`;
  "Predicate" framing removed.
- **`ConceptAgentLoadTest`** (renamed from `PredicateEngineLoadTest`) — the
  reference-engine half (`RefConcept` + `referenceEngineThroughput`) is deleted;
  the chain-throughput path is retained.
- **`ConceptTestBase`**, concept tests (`UserLookupByUsernameTest`,
  `PasswordAuthCheckTest`, `SessionGrantTest`) — unchanged constructors, no change.
- **`LegibleArchitectureRulesTest`** `r5` — scans `extends ConceptAgent` (unchanged
  text, now matches the merged class).

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Sync evaluation is the only concept path | unit | `ConceptAgentTest`, `ConceptAgentLoadTest`, concept tests | pass | 78/78 green |
| Full login flow still resolves (200/401) | flow-regression | `CucumberTest`, `DebugControllerTest`, `EngineTimingTest` | pass | 78/78 green |
| Concurrency unaffected (single-writer tick lock retained) | integration | `ConcurrencyTest` | pass | 0 errors 1–32 threads |
| No reference-engine code remains | unit | grep `engine/predicate/`, `engine.mode`, `PredicateConceptAgent` | pass | 0 matches |
| Full regression | integration | `verify_artefacts.py && mvn test` | pass | 78 tests, 0 failures |

## Gates

### Design gate

Approve with `./clad approve-maintenance single-engine design` after reviewing
the design + non-goals above.

### Evidence gate

Approve with `./clad approve-maintenance single-engine evidence` after the test
matrix is green.

## Notes

- **Non-goal:** this change does not alter concept/sync SPARQL, the action log,
  storage mapping, or flow-token lineage. It is purely an engine consolidation.
- **`SyncDispatcher` naming:** after the merge it is the only dispatcher and keeps
  its name (used by controllers, `SyncAgent`, `DebugController`).
- The read-then-write race fix (tick lock) from v0.1.6 is retained unchanged.
