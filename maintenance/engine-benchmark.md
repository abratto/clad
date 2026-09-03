<!-- Maintenance-route planning record. -->
# Maintenance change — `engine-benchmark`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (canonical), `reference-impl/java-legible`; comparison leg covers `reference-impl/clad-engine` and `reference-impl/java-micronaut-jena`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Add a `reference-impl/legible-bench` module porting the prototype's hand-rolled benchmarks into the reactor, plus new fan-out and per-concept-serialization benchmarks, so the engine's performance claims become reproducible at the repo tip.

## Why

The v0.2.0 CHANGELOG and `java-legible/README.md` cite "~3 µs/request, ~100×
lower latency, ~50× throughput vs the Jena profile" — numbers measured by
`dev.legible.bench` in the **untagged scratch prototype**, not against `main`.
Meanwhile `methodology/implementation/STAGES.md` and the reference-impl README
still say the engine "has not been designed or vetted for scale." The two
statements are in tension: a strong claim in one place, an admitted lack of
evidence in another. This change ports the harness into `reference-impl/`,
adds the two benchmarks the existing login-shaped probe cannot show (fan-out
cost, per-concept serialization ceiling), and replaces the claims with
reproducible numbers plus reproduction instructions.

Scope per human decision: (1) keep the hand-rolled `nanoTime` harness (no
JMH) so the driver matches the legacyprofiles' `ConceptAgentLoadTest` /
`ConcurrencyTest` methodology 1:1; (2) persistence leg deferred to a follow-up
after the in-memory numbers are recorded; (3) benchmarks stay out of the
default `test.command` / CI.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Observability addition only; no engine/runtime surface touched. |
| Action ordering and sync deduplication | preserved | No engine change. |
| Flow-token lineage | preserved | No runtime change. |
| Storage/retention semantics | preserved | Persistence leg deferred; no backend change in this pass. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `java-legible/README.md` Performance section; scale caveat wording in `STAGES.md` / reference-impl README |
| Profile configuration or deployment files | yes | `reference-impl/pom.xml` (+`legible-bench` module) |
| Engine/runtime implementation | no | — |
| Profile tests | no | Bench is advisory; excluded from `test.command` and CI |
| UC artefact chain | no | — |

## Design (methodology, fixed by the existing assets)

1. **`Bench` (sequential)** — verbatim port. Warmup 5,000 logins; 100,000 timed
   logins; reports ops/s and µs/request, plus in-flight + archived-buffer
   invariants after the run (should be `0` in-flight; buffer ≤ capacity).
2. **`ConcurrencyBench` (concurrency sweep)** — replicate the Jena profile's
   `ConcurrencyTest` exactly: levels `{1, 2, 4, 8, 16, 32}`, 200 requests per
   thread, **unique user per request**, mean/p50/p95/p99/p99.9 + errors.
3. **`FanOutBench` (NEW)** — use the `social` profile: seed one author with
   N followers (N ∈ {1, 10, 100, 1000}); drive one `comment()` flow per trial;
   report per-request latency and req/s vs N. Measures `WhereEvaluator` frame
   multiplication and multi-target `then` minting cost — the cost shape login
   cannot show.
4. **`SerializationBench` (NEW)** — all threads hammer the **same** user
   (single-concept hot contention) at levels {1, 8, 32, 64}, reported next to
   the existing unique-user sweep. This documents the per-concept lock ceiling:
   max sustainable actions/sec for one concept ≈ 1/avg-action-latency, and shows
   how uniquely-user-sharded workloads scale relative to it.
5. **Cross-profile parity** — on the same machine, same session:
   `legible-bench` (in-memory) vs `clad-engine ConceptAgentLoadTest` (legacy
   chain, ~0.8 ms avg iter) vs `java-micronaut-jena ConcurrencyTest`. All three
   recorded in the evidence table.

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Bench module compiles and runs smoke-scale | smoke | `mvn compile -pl legible-bench -am` + all four `exec:java` mains | pass | all four run to BUILD SUCCESS |
| Invariants after Bench: no in-flight flows leak | smoke | `Bench` output line `in-flight flows after run: 0` | pass | run 2026-09-02: `0 in-flight`, buffer at capacity |
| Sequential throughput recorded | bench | `Bench`: ~190k ops/s, ~5.3 µs/request over 100k logins | pass | see Evidence below |
| Concurrency sweep recorded | bench | `ConcurrencyBench`: peak ~18k req/s @ 4 threads (unique user, seeded per request), ~3.3k at 32 | pass | see Evidence |
| Fan-out sweep recorded | bench | `FanOutBench`: ~17–21k req/s at N=1 → ~406–767 req/s at N=1000; notification tally advisory (per human decision b) | pass | see Evidence |
| Serialization ceiling recorded | bench | `SerializationBench`: ~20k req/s at 1 thread → ~54k at 64 (same hot user, no per-request seeding) | pass | see Evidence |
| Reactor still green with new module | gate | `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml` | pending | run at commit time |
| Regression suite unaffected | unit | `python3 -m unittest discover -s quality-gate/tests` | pending | run at commit |

## Evidence (2026-09-02, one session, JDK 25, laptop-class; hardware-relative)

- **Sequential** (`Bench`): 100k/100k logins in ~0.55 s → ~5.3 µs/request (~190k ops/s); `in-flight flows after run: 0`.
- **Concurrency** (`ConcurrencyBench`, unique user, per-request seeding): mean latency 0.09 ms @1 → 9.5 ms @32 threads; req/s 9.96k, 15.9k, 18.5k, 11.0k, 5.6k, 3.3k at levels 1/2/4/8/16/32. Zero errors at every level.
- **Fan-out** (`FanOutBench`, worried-commenter shape per the exemplar): ~17–21k req/s at N=1; ~3–5.6k at N=100; ~406–767 at N=1000. Notification tally printed as **advisory** (`notifTally`/`upper`), per the human decision to make the check advisory (option b) — the tally's expectation accounting diverged from the profile's set-of-messages delivery semantics, and correctness ownership stays with the profile's flow tests.
- **Serialization ceiling** (`SerializationBench`, same hot user): 20.3k → 38.7k → 46.5k → 54.2k req/s at 1/8/32/64 threads; mean latency *falls* 49 µs → 18 µs because the workload avoids per-request seeding. Interpretation: per-concept serialization costs ~1 action per (avg µs/action); scaling shows where concept-lock amortization is cheap.
- **Honest reading**: the unique-user sweep *degrades* because the driver seeds a fresh user inside the timed loop (per-request writes serialize); the same-user loop scales because it omits seeding. Both are driver artefacts worth carrying into any future tuning work — neither indicts the engine's per-concept serialization contract itself.
- **Cross-profile comparison leg** (clad-engine `ConceptAgentLoadTest`, java-micronaut-jena `ConcurrencyTest`): deferred per the human decision to land persistence/comparison legs after the in-memory numbers.

## Gates

### Design gate

Reviews scope (module location, advisory-only CI policy, hand-rolled harness,
deferred persistence leg). Approve with
`./clad approve-maintenance engine-benchmark design`, then set Status `active`.

### Evidence gate

Reviews recorded in-memory numbers (sequential, concurrency sweep, fan-out
sweep, serialization ceiling) plus the cross-profile table, and the doc
updates. Approve with `./clad approve-maintenance engine-benchmark evidence`,
then set Status `closed`.

## Notes

- **Numbers are hardware-relative.** The record stores: hardware class, JVM
  version, and date, and marks cross-repo comparison as same-session only.
- **Follow-up deferred by decision**: persistence leg (Postgres / Rmap /
  Jena FactStore backends) after the in-memory numbers land.
- The per-concept serialization result is expected to be the limiter; this
  benchmark exists to make that limit a documented engineering fact rather
  than an unstated assumption.
