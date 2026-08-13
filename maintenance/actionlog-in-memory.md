# Maintenance change — `actionlog-in-memory`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Make the action log always in-memory and replace the archive graph with a pluggable log sink.

## Why

The action log is transient execution state — high-churn writes,
short-lived data, syncs needing fast atomic reads. Keeping it on TDB2
caused 1 GB/day disk growth (tombstones from DELETEs never free physical
space). The archive graph also grew unbounded when `engine.archive.flows=true`.
Neither should exist on durable storage.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Concept completion SPARQL unchanged; Web/respond contract untouched |
| Action ordering and sync deduplication | preserved | Sync WHERE clauses still read the action log (now in-memory); dedup guard unchanged |
| Flow-token lineage | preserved | Flow tokens still span the action chain; flush-before-delete retains traceability in the sink |
| Storage/retention semantics | changed | Completed flows are flushed to a `FlowArchiveSink` then deleted; no archive graph. Deliberate change — see Notes. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `clad.properties` (engine.archive.sink replaces engine.archive.flows), Dockerfile/compose env |
| Profile configuration or deployment files | yes | `clad.properties`, `docker-compose.yml` |
| Engine/runtime implementation | yes | FlowArchiveSink/LoggerSink/DevNullSink (new), Storage/LocalStorage/RemoteStorage (archive removed), SplitStorage (default), CladDatasetFactory (rewritten), FlowArchiver (sink-based), Application (EngineConfig removed), RdfVocabulary (archive IRI removed), DebugController (archive graph removed), SyncDispatcher (tick-lock serialization) |
| Profile tests | yes | StorageArchiveFlowTest, SplitStorageTest, CladDatasetFactoryTest, DebugControllerTest, PredicateEngineTest |
| UC artefact chain | no | No concept/sync/spec slice changes; storage mapping is profile-specific (Stage 04a) |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Action log always in-memory; sync reads work | integration | `SplitStorageTest`, `DebugControllerTest` | pass | 79/79 green |
| Completed flow flushed then deleted (no archive graph) | unit | `StorageArchiveFlowTest`, `SplitStorageTest` | pass | 79/79 green |
| Remote backend still fails closed / routes business graphs | unit | `CladDatasetFactoryTest`, `StorageArchiveFlowTest` | pass | 79/79 green |
| Concurrent logins produce zero errors under load | integration | `ConcurrencyTest` (1–32 threads) | pass | 0 errors at every level; see Notes |
| Full regression | integration | `python3 quality-gate/verify_artefacts.py && mvn test` | pass | 79 tests, 0 failures |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before a
maintenance-scoped implementation or deployment file changes. Approve with
`./clad approve-maintenance <change-name> design`, then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- **Storage/retention semantics is a deliberate change** (not "preserved" in
  the Contract impact table above because the archive graph is removed). The
  feature contract (action outcomes, sync rules, flow-token lineage) is
  preserved; only the *retention backend* changes. Projects using
  `engine.archive.flows=true` must migrate to `engine.archive.sink=logger`
  + the debug buffer.
- `S3Sink` is deferred — it needs an AWS SDK dependency decision, not part of
  this change. The `FlowArchiveSink` interface already accommodates it.
- **Concurrency fix (discovered via this change).** Making the action log
  in-memory exposed a pre-existing dispatch-loop race: `findPendingInvocations`
  dedups with `FILTER NOT EXISTS { :outcome }` at read time, so concurrent
  ticks could both see an action as pending and process it twice, producing
  duplicate `respond` actions and cross-flow field contamination (a 401 body
  carrying a `sessionToken`). A single-writer lock at the storage layer did
  NOT fix this — it serialized individual SPARQL ops but not the
  read→write cycle. The fix is a fair `ReentrantLock` in
  `SyncDispatcher.runTick()` serializing the whole quiescence iteration.
  Result: `ConcurrencyTest` went from 1103 errors @ 8 threads (929 @ 16) to
  0 errors at every level through 32 threads, with throughput improving from
  ~30 req/s (2 threads) to ~195 req/s and mean latency dropping from 65 ms to
  ~9 ms at 2 threads. TDB2-mem was also benchmarked and rejected (stalls at
  concurrency 4 with `BlockMgrCache - write: Block in the read cache`).
