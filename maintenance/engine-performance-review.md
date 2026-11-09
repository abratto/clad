<!-- Maintenance-route planning record. -->
# Maintenance change — `engine-performance-review`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-engine`, `reference-impl/legible-storage`, `reference-impl/java-legible`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Add a JMH benchmark module alongside the existing hand-rolled `legible-bench`, measure the in-memory engine and the Postgres `FactStore`, profile allocation/GC/lock behaviour, and publish a ranked performance-findings report — no engine, storage, concept, or sync semantics change.
- **Dependent re-entry:** `none`

## Why

The engine's performance claims are recorded from a one-session, hand-rolled
`nanoTime` harness (`maintenance/engine-benchmark.md`; `reference-impl/java-legible/README.md`
§Performance) and are explicitly hardware-relative and advisory. The roadmap
still carries "Production workload characterization — benchmark the predicate
engine with a durable backend, realistic graph sizes and action chains, mixed
read/write traffic, and sustained concurrency" as backlog. A static read of the
engine and storage layer surfaces several untested hypotheses:

- **Per-completion log scans.** `matchConjuncts` and `hasEmission` rescan the
  flow log per candidate rule; `InMemoryActionLog` lookups are linear
  (`SyncEngine.java:131-165`, `InMemoryActionLog.java`). Fan-out flows grow
  O(N) actions, so the cost may trend O(N²) even though the recorded fan-out
  curve is described as "roughly linear".
- **Frame-map copying.** `WhereEvaluator` copies the whole frame map per
  fan-out row (`WhereEvaluator.java:271-328`).
- **Region scans and copies.** `InMemoryRegion.subjects` scans every subject
  per fan-out; `read` copies the value set on every hit and scans the whole
  region on a miss (`InMemoryFactStore.java`).
- **Per-request archival cost.** `FlowArchiver.archive` scans and copies the
  flow twice plus a synchronized buffer add (`FlowArchiver.java`,
  `FlowArchiveBuffer.java`).
- **Durable backend gap.** `PostgresFactStore` opens a connection and issues
  one autocommit statement per read/write, with no pooling, batching, or
  per-action transaction, and the primary key cannot serve
  `subjects(predicate,value)` or `facts()` scans (`PostgresFactStore.java`).

This record governs the measurement work needed to confirm or refute those
hypotheses. It deliberately does **not** authorise optimisations.

## Mechanism

This change adds a benchmark harness; it does not alter an engine or profile
code path. The measurement targets are the existing paths above. The harness:

- lives in a new reactor module `reference-impl/legible-bench-jmh`, kept
  alongside `reference-impl/legible-bench` so the recorded 2026-09-02 baseline
  stays directly comparable;
- uses `jmh-core` + `jmh-generator-annprocess`, isolated to that module;
- benchmarks login throughput, fan-out scaling (N ∈ {1, 10, 100, 1000}),
  concept contention (same-user vs unique-user at `@Threads` {1, 4, 16, 64}),
  region micro-operations, and `where` frame multiplication;
- runs the Postgres leg against a Testcontainers-managed PostgreSQL
  (`testcontainers.version` is already pinned in `reference-impl/pom.xml`),
  with a `-Dpostgres.url` override for an external database;
- captures JFR CPU/allocation/GC/lock profiles for the end-to-end benchmarks.

Benchmarks remain advisory and outside `test.command`/CI, matching the existing
`engine-benchmark` policy.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Harness only; no engine/runtime source change |
| Action ordering and sync deduplication | `preserved` | Harness only; no engine/runtime source change |
| Flow-token lineage | `preserved` | Harness only; no engine/runtime source change |
| Storage/retention semantics | `preserved` | Harness only; no storage source change |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `reference-impl/java-legible/README.md` §Performance gains JMH reproduction notes and any reconciled claim; `maintenance/engine-performance-review.md` evidence |
| Profile configuration or deployment files | yes | `reference-impl/pom.xml` adds the `legible-bench-jmh` module |
| Engine/runtime implementation | no | Measurement only — no `legible-engine` or `legible-storage` source change |
| Profile tests | no | Benchmarks are not tests and stay out of CI |
| UC artefact chain | no | No outcome, contract, sync, or ordering change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| JMH module compiles and a smoke run completes | smoke | `mvn -f reference-impl/pom.xml -pl legible-bench-jmh -am -DskipTests package` + JMH smoke run | pass | BUILD SUCCESS; `benchmarks.jar` lists 12 benchmarks; smoke run completed |
| In-memory baseline recorded | bench | `legible-bench-jmh` login + fan-out + contention + region | pass | `docs/experiments/engine-performance-review.md` §Results |
| Postgres leg recorded | bench | `legible-bench-jmh` against Testcontainers PostgreSQL | pass | `docs/experiments/engine-performance-review.md` §Results (44 ops/s login) |
| No engine/runtime source change | gate | `git diff --stat` shows harness/docs only | pass | only `reference-impl/pom.xml` (+1 module) and new harness/docs files |
| Artefact gate stays green | integration | `python3 quality-gate/verify_artefacts.py` | pass | exit 0, "artefact pipeline intact" |
| Reactor tests stay green | unit | `mvn test -f reference-impl/pom.xml -pl java-legible -am` | pass | 47 tests, 0 failures, 0 errors |

## Evidence

Recorded 2026-11-09, JDK 25.0.2, macOS, Postgres 16 via Testcontainers. Full
tables and JFR attribution live in `docs/experiments/engine-performance-review.md`.

- **In-memory login:** 256,133 ops/s JMH (219,306 ops/s hand-rolled cross-check),
  17,570 B/op.
- **Fan-out:** 220,730 ops/s at N=1 → 1,737 ops/s at N=1000; 18 KB → 1.9 MB/op.
  Linear in N beyond N=10; the suspected O(N²) was **refuted**.
- **Region primitives:** `subjects` 95k → 9.8k ops/s and `read` miss 323k →
  29.6k ops/s from 1k → 10k subjects — both are full region scans.
- **Postgres:** 44 ops/s login, ~3 ms per primitive — connection-per-operation
  dominates.
- **JFR:** `SecureRandom`/UUID ~13–19% of samples; `LinkedHashMap` copies 33%
  of fan-out allocation.
- **No engine or storage source changed.** All candidates are deferred to
  separate R20 records.

## Gates

### Design gate

The human reviews scope, the no-optimisation non-goal, harness placement, the
Postgres/Testcontainers approach, and the test matrix before any module is
added. Approve with
`./clad approve-maintenance engine-performance-review design`, then set Status
to `active`.

### Evidence gate

The human reviews the recorded JMH/JFR evidence, the ranked findings, and the
green artefact/reactor gates before commit. After approval, set Status to
`closed` and commit the record with the harness.

## Notes

- **Non-goal:** implementing optimisations. Candidates found are reported with
  impact/effort/risk and an R20 classification; none is applied in this pass.
- **Comparability:** JMH numbers are not directly comparable to the hand-rolled
  2026-09-02 baseline; both harnesses are kept so shape and absolutes can be
  read separately.
- **Advisory only:** benchmarks stay out of `test.command` and CI.
- **Hardware-relative:** evidence records JDK, CPU, RAM, and date; cross-profile
  comparisons are same-session only.
- **Rollback:** removing the module from `reference-impl/pom.xml` and deleting
  the directory restores the prior tree; no runtime state or contract changes.
