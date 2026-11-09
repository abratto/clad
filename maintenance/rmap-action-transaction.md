<!-- Maintenance-route planning record. -->
# Maintenance change — `rmap-action-transaction`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-storage`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Wrap `RmapRegion.flushAction` in one database transaction (one connection per concept action, atomic flush) and record why the proposed `INSERT … ON CONFLICT DO UPDATE` rewrite is declined in favour of the existing update-then-insert.
- **Dependent re-entry:** `none`

## Why

Phase 0 of `postgres-hikari-pool` moved Postgres from ~43 to ~1,800 login ops/s
with Hikari, and left ~70–150 µs per primitive. `RmapRegion.flushAction`
currently executes each buffered row on its own autocommit connection
(`RmapPostgresFactStore.java:313`), so one concept action can borrow several
connections and a mid-flush failure can leave a partially applied action.

The original plan also proposed replacing `fetchCount` + update/insert with a
single `INSERT … ON CONFLICT DO UPDATE`. The store already documents why that is
unsafe: PostgreSQL validates `NOT NULL` on the **proposed insert tuple** before
resolving the conflict, so a partial upsert of an existing multi-column row is
rejected for its absent mandatory sibling even though the row exists
(`RmapPostgresFactStore.java:749-757`). The update-then-insert path exists to
avoid that. This change therefore keeps update-then-insert and takes only the
safe part: the per-action transaction.

## Mechanism

- `RmapRegion.flushAction` opens one `dsl.transaction(...)` and passes the
  transactional `DSLContext` to `flushSubject`/`flushRow`, so every row of one
  concept action shares one connection and commits atomically.
- `abortAction` remains a buffer discard (no writes were issued before flush).
- `flushRow` keeps `fetchCount` + update/insert; no SQL semantics change.
- A later change may evaluate a single-statement CTE
  (`WITH updated AS (UPDATE … RETURNING 1) INSERT … WHERE NOT EXISTS …`) or
  batching, but only with tests proving the mandatory-column behaviour is
  preserved. That is out of scope here.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No concept/sync/outcome change |
| Action ordering and sync deduplication | `preserved` | Engine unchanged |
| Flow-token lineage | `preserved` | Engine unchanged |
| Storage/retention semantics | `preserved` | Same schema and facts; per-action atomicity is strengthened to match the documented "action is the atomic unit" contract |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `docs/experiments/engine-performance-review.md` addendum; this record |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `RmapPostgresFactStore.RmapRegion.flushAction` / `flushSubject` / `flushRow` |
| Profile tests | yes | `legible-storage` Rmap suite; new atomicity/rollback test |
| UC artefact chain | no | No outcome, contract, sync, or ordering change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Rmap semantics unchanged | integration | `mvn -f reference-impl/pom.xml -pl legible-storage test` | pass | 32 tests, 0 failures |
| One action commits atomically | integration | `aConceptActionFlushCommitsOrRollsBackAsOneUnit` | pass | duplicate-username flush rolls the first row back |
| Login throughput not materially regressed | bench | `PostgresBenchmark.login -p pool=hikari -p store=rmap` | pass | 1,484 ± 355 vs 1,823 ± 369 before (within noise) |
| Hikari-backed store works | integration | `storeRunsOnAHikariPool` | pass | login flow green over a pooled DataSource |
| No engine source change | gate | `git diff --stat` | pass | only `legible-storage` + tests/records |
| Artefact gate stays green | integration | `python3 quality-gate/verify_artefacts.py` | pass | exit 0, pipeline intact |

## Evidence

- `RmapRegion.flushAction` now runs inside one `dsl.transaction(...)`; the
  buffered rows of a concept action share one connection and commit atomically.
- `legible-storage`: 32 tests, 0 failures (was 30; added the atomicity and
  Hikari-fixture tests).
- JMH `PostgresBenchmark.login` (hikari/rmap): 1,484 ± 355 ops/s vs 1,823 ± 369
  before. The difference is inside the error bars at this sample size; the
  transaction's value is per-action atomicity, not throughput.
- **Declined:** `INSERT … ON CONFLICT DO UPDATE` — PostgreSQL validates
  `NOT NULL` on the proposed insert tuple before resolving the conflict
  (`RmapPostgresFactStore.java:749-757`), so the existing update-then-insert
  stays.
- **Phase 3 not triggered:** with Hikari, `readHit` is ~72 µs/op while a pool
  borrow is a few µs, so action-scoped read connections would not move the
  needle. The remaining cost is SQL/jOOQ, not connection acquisition.

## Gates

### Design gate

The human reviews the narrowed scope (transaction only; upsert declined for the
documented `NOT NULL` hazard) and the test matrix. Approve with
`./clad approve-maintenance rmap-action-transaction design`, then set Status to
`active`.

### Evidence gate

The human reviews the Rmap suite, the rollback test, and the before/after JMH
numbers. Approve with
`./clad approve-maintenance rmap-action-transaction evidence`, then set Status to
`closed`.

## Notes

- **Declined:** naive `INSERT … ON CONFLICT DO UPDATE` for the reason above.
- **Deferred:** CTE update-or-insert and multi-row batching, only with
  mandatory-column regression tests.
- **Rollback:** remove the transaction wrapper; no schema change.
