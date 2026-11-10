<!-- Maintenance-route planning record. -->
# Maintenance change — `per-subject-concept-locking`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `active` (`draft` until design approval, `active` while implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-engine`, `reference-impl/legible-storage`, `reference-impl/java-legible`, `reference-impl/legible-bench-jmh`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Replace the per-concept action lock with per-subject (lock-key) striped locks, make `RmapRegion`'s action buffer thread-local, declare subject keys on the example concepts, and add a throwaway concurrency lab plus Step 0 timing/benchmarks.
- **Dependent re-entry:** `none`

## Why

Step 0 (`ConceptTimingProbe`, Hikari/Rmap, login flow) showed the
`PasswordAuth` concept lock at ~99% utilisation at 4 threads
(`action + flush` ≈ 0.99 of wall), with `same` and `unique` users both
plateauing at ~2.3k login/s. The engine's per-concept lock serializes every
login on `UserNaming`, `PasswordAuth`, and `Session` regardless of user, so
unique subjects cannot scale. The lab app confirms the strategy: unique subjects
scale, the same subject does not.

## Mechanism

- **`Concept` contract:** `stateful()` (default true), `lockKey(action,input)`
  (default null = concept-wide), `lockKeys(action,input)` (multi-subject).
- **`ConceptLocks`:** striped `ReentrantLock`s keyed by `(concept, key)`;
  multi-subject actions acquire sorted stripe indices and release in reverse
  (global order, no deadlock); `stateful()==false` takes no lock.
- **`SyncEngine.execute`:** acquires the declared keys and runs the existing
  begin/execute/flush/abort body (`runAction`); stateless concepts skip the
  region lookup and the lock.
- **`RmapRegion`:** the action buffer/buffering flag becomes a `ThreadLocal`, so
  concurrent actions on different subjects do not share a buffer. The
  one-transaction-per-action flush is unchanged.
- **Lock keys:** login (`username`, `userId`, `sessionId`); social/tagging/token
  concepts declare their subject; `Web` is stateless. Unannotated concepts keep
  the safe concept-wide lock.
- **Lab app:** `dev.legible.bench.concurrency` (throwaway): counter (same
  subject), accounts (unique + multi-subject transfer), custom Rmap schemas,
  `ConcurrencyLabProbe` (correctness), `ConcurrencyLabBenchmark` (throughput).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No concept/sync outcome change; all existing flow tests green |
| Action ordering and sync deduplication | `preserved` | Per-flow order unchanged; lock acquisition is internal |
| Flow-token lineage | `preserved` | Engine provenance untouched |
| Storage/retention semantics | `preserved` | Same schema/facts; Rmap flush is still one transaction per action |

**Concurrency semantics change:** actions on the same concept but different
declared subjects may now run concurrently; actions on the same subject remain
serialized. Sync `where` reads remain unlocked (per-action atomicity, not
flow-snapshot isolation). The generic `PostgresFactStore` remains best-effort
(no `TransactionalRegion`); the guarantee is validated on in-memory and Rmap.

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `docs/experiments/engine-performance-review.md`; this record |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `Concept`, `ConceptLocks` (new), `SyncEngine`, `RmapPostgresFactStore` |
| Profile tests | yes | engine lock tests, storage buffer isolation, login/social concurrency suites |
| UC artefact chain | no | No outcome, contract, sync, or ordering change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Same key serializes; different keys overlap | unit | `ConceptLocksTest` | pass | same-key blocks; different-stripe acquires while held |
| Multi-key acquisition is ordered/deadlock-free | unit | `ConceptLocksTest` | pass | forward/reverse key sets complete |
| Engine applies per-subject locks | unit | `SyncEngineLockTest` | pass | different keys overlap; same key maxInFlight=1 |
| Stateless concept skips region/lock | unit | `SyncEngineLockTest` | pass | throwing FactStore never called |
| Thread-local Rmap buffers isolate subjects | integration | `RmapPostgresFactStoreTest.concurrentActionsOnDifferentSubjectsKeepSeparateBuffers` | pass | both rows written, no cross-contamination |
| Existing storage suite | integration | `mvn -f reference-impl/pom.xml -pl legible-storage test` | pass | 33 tests |
| Existing engine/login/social suites | integration | `mvn -f reference-impl/pom.xml -pl java-legible -am test` | pass | includes same-user lockout and mixed concurrency |
| Lab invariants (memory) | integration | `ConcurrencyLabProbe -Dlab.store=memory` | pass | counter/account/transfer exact |
| Lab invariants (Rmap) | integration | `ConcurrencyLabProbe -Dlab.store=rmap -Dlab.pool=hikari` | pass | counter/account/transfer exact, no deadlock |
| Unique subjects scale; same subject does not | bench | `ConcurrencyLabProbe` + `PostgresConcurrencyBenchmark` | pass | see Evidence |
| Artefact gate | gate | `python3 quality-gate/verify_artefacts.py` | pass | exit 0 |

## Evidence

Step 0 (before B), Hikari/Rmap, login flow: `PasswordAuth` lock ~0.99 of wall at
4 threads; same and unique both ~2.3k login/s.

After B:

| Workload | 1 thread | 4 threads |
|---|---|---|
| Lab counter, same subject (Rmap) | 2,318/s | 2,859/s |
| Lab counter, unique subjects (Rmap) | 2,443/s | 7,517/s |
| Lab accounts, unique (Rmap) | 2,584/s | 8,194/s |
| Lab transfer, multi-subject (Rmap) | 1,574/s | 4,618/s |
| Login JMH, same user | 1,298/s | 2,134/s |
| Login JMH, unique users | 1,347/s | 3,596/s |

The lab confirms the strategy: unique subjects scale ~3×, the same subject stays
flat, and multi-subject transfers scale without deadlock. The login flow gains
~50% for unique users (2,405 → 3,596/s) because its next bottleneck is DB
flush/round-trip cost (`PasswordAuth/flushAction` and `Session/flushAction`
utilisation exceeds 1.0 at 4 threads), not the lock.

## Gates

### Design gate

Review the `Concept` API additions, the striped-lock design, the thread-local
Rmap buffer, the lock-key mapping, and the test matrix. Approve with
`./clad approve-maintenance per-subject-concept-locking design`, then set Status
to `active`.

### Evidence gate

Review the before/after numbers, the lab invariants, and the green suites.
Approve with `./clad approve-maintenance per-subject-concept-locking evidence`,
then set Status to `closed`.

## Notes

- **Single-process only.** In-process locks do not coordinate across JVMs;
  multi-instance needs partitioning, DB row locks, or optimistic concurrency.
- **Sync reads** are not isolated; per-action atomicity is preserved.
- **Striping** uses 4096 locks; false contention is possible but bounded.
- **Lab app is throwaway**; remove it after the experiment, keeping the findings.
- **Generic PostgresFactStore** is best-effort (no per-action atomic flush).
