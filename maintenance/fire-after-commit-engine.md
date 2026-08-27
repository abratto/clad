# Maintenance change — `fire-after-commit-engine`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `mixed`
- **Status:** `closed`
- **Affected profile(s):** `all profiles` — the engine/runtime is re-architected; `java-micronaut-jena` and `java-micronaut-postgres` become `FactStore` implementations of a new shared engine, plus a new canonical in-memory profile
- **Feature-contract impact:** `re-entered`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Replace the transactional-predicate RDF/SPARQL engine with a paper-faithful "fire-after-commit" engine — concepts hold state as relations behind a `FactStore` SPI, actions are map→map, syncs are declarative `when/where/then` rules, and coordination happens after an action is committed to a structured action log (no transactions, no rollback).

## Why

The current engine encodes the older "sync-as-transaction" reading of
Jackson's *Essence of Software*: `ConceptAgent.writeCompletion` performs an
"atomic composite write" (completion + downstream syncs in one Jena transaction,
with `abortBatch` rollback), `SyncEvaluator` documents "commits or rolls back
atomically", and `ENGINE.md` calls it a "transactional predicate engine".

Daniel Jackson's own forum reply records that his student Eagon Meng's sync DSL
"gets rid of the need for transactions, and also allows much finer granularity"
(see `arxiv.org/abs/2508.14511` and `arxiv.org/abs/2606.11051`). The mature model:
- **Ontology** — individuals (UUIDs), values, actions (atomic, map→map), facts (relations).
- **Sync DSL** — declarative `when` / `where` / `then`, with the `where` clause
  binding facts and doubling as the guard.
- **Fire-after-commit** — syncs fire only after an action is committed to the
  log; the log records invocation + completion with provenance edges; every
  action enters the log only by way of a sync's `then` clause. No transactions,
  no rollback; failure is a named outcome, not an exception to roll back.

A scratch prototype (`scratch/legible-engine-prototype/`, 53 tests) proved the
semantics against UC-00-login with **behavioural parity** (identical HTTP codes
and field values, verified by `FlowTraceTest` and `LoginFlowTest`), exercised
fan-out, Pattern D reads, `OPTIONAL`, `?_eachthen` aggregation, `bind(uuid())`,
route scoping, replay, archival, and concurrency — and measured ~100× lower
latency than the Jena profile. This change lands that prototype formally.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Identical outcomes (`FOUND`/`OK`/`BAD_PASSWORD`/`LOCKED`/`GRANTED`/`refused`) and HTTP responses (200/401 + `sessionToken`/`message`); parity proven by `FlowTraceTest` + `LoginFlowTest` |
| Action ordering and sync deduplication | changed | Syncs now fire **after** commit (was: atomically with completion); dedup is provenance-based (`parentActionId` + `causedBySync`) instead of `FILTER NOT EXISTS { ?_when_1 :syncName [] }`. Observable chain order preserved (chain table ↔ runtime, `FlowTraceTest`); exactly-once still holds |
| Flow-token lineage | changed | Bare UUID IRI + RDF-star `<< :outcome >> :flow` annotation → structured record (id/parent/action/actor/at/outcome/payload) with `parentActionId` + `causedBySync` provenance edges. Observable lineage preserved |
| Storage/retention semantics | changed | RDF/Jena substrate → `FactStore` SPI (in-memory canonical profile); archival = flush to a sink + bounded buffer, then discard the transient per-flow log. Jena/Postgres become `FactStore` implementations |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `ENGINE.md`, `TRACEABILITY.md`, `ARTEFACT_MAP.md`, `SYNCHRONIZATIONS.md`, `SYNC_PATTERNS.md`, `FLOW_TOKENS.md`, `WEB_CONCEPT.md`, `SYNC_LOWERING.md` (rewritten), `AGENTS.md` §5/§9 (retire R10, R21; reword R12) |
| Profile configuration or deployment files | yes | `clad.properties` — `storage.layer`, `engine.*`, `sync.impl.dir`/`concept.impl.dir`/`test.source.root` |
| Engine/runtime implementation | yes | New shared engine (`FactStore`/`Region`, `ActionLog`, `Concept`, `SyncRule`, `WhereEvaluator`, `SyncEngine`, `FlowArchiver`, `DebugApi`); Jena/Postgres profiles re-implement the `FactStore` SPI |
| Profile tests | yes | New engine/matcher/semantics/debug/parity/concurrency suites; login re-derived as `Concept`/`SyncRule` |
| UC artefact chain | yes | 01–03b, 04b, 04c preserved; 04a storage mapping and 04d/04e implementation re-lower; 05 trace re-derived (new debug surface). See `_changes/` matrix |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Behavioural parity with UC-00-login | flow-regression | `FlowTraceTest` + `LoginFlowTest` (chain table ↔ runtime, 200/401 + fields) | pass | 53 tests, 0 failures (java-legible) |
| Sync semantics (fan-out, Pattern D, OPTIONAL, aggregation, bind(uuid)) | integration | social + tagging + token flow tests | pass | green (java-legible) |
| Fire-after-commit, replay, archival, route scoping | unit | `EngineSemanticsTest`, `WhereEvaluatorTest`, `DebugApiTest` | pass | green (legible-engine + java-legible) |
| Concurrency correctness | integration | `ConcurrencyTest` (login/tagging/token), lost-update + isolation | pass | deterministic across repeated runs |
| Full regression gate | integration | `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml` | pass | artefact gate green; legible-engine/java-legible/jena green (Postgres needs Docker, not exercised) |

## Gates

### Design gate

The human reviews contract impact, the test matrix, and the engine design before
any engine/profile/configuration surface is modified. Approve with
`./clad approve-maintenance fire-after-commit-engine design`, then set Status to `active`.

### Evidence gate

Approve with `./clad approve-maintenance fire-after-commit-engine evidence` after
the test matrix is green, then set Status to `closed` and commit the record with
the change.

## Notes

- **Open decision — Web naming:** the prototype uses the paper's `Web/request`
  (the current runtime name; specs say `Web/handle`). Reconciling the specs to
  `Web/request` collapses the "bootstrap handoff exception" and re-enters 01b/03.
  Default: reconcile (paper fidelity); flag as a small mechanical re-derivation.
- **Open decision — Jena/Postgres profiles:** port both to `FactStore`
  implementations (default), or defer one. Durability of the action log remains a
  deferred follow-up (in-memory for now).
- **Rollback boundary:** the scratch prototype remains intact until the engine is
  landed; the Jena/Postgres profiles stay green until re-lowered.
