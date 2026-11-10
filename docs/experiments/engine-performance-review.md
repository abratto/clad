# Engine performance review (in-memory + Postgres)

**Date:** 2026-11-09
**Engine:** `reference-impl/legible-engine` (fire-after-commit, `FactStore` SPI)
**Storage:** `InMemoryFactStore` and `PostgresFactStore`
**Harness:** `reference-impl/legible-bench-jmh` (JMH 1.37), plus the existing
`reference-impl/legible-bench` hand-rolled probes for continuity
**Governed by:** `maintenance/engine-performance-review.md` (R20)

> **Scope.** This is a measurement record. It reports findings and ranked
> optimisation candidates; it does **not** change engine, storage, concept, or
> sync behaviour. Each candidate below needs its own R20 design gate.

## Environment

| Item | Value |
|---|---|
| JDK | Temurin 25.0.2 (compiled `--release 21`) |
| Maven | 3.9.16 |
| OS | macOS (darwin) |
| Postgres | `postgres:16-alpine` via Testcontainers 1.20.4 |
| Harness | JMH 1.37, `@Fork(1)`, 3 warmup / 5 measurement iterations (in-memory), 2/3 (Postgres) |

Numbers are hardware-relative. Treat **shape** and **allocation per operation**
as the findings; absolutes are one machine on one day.

## Reproduction

```bash
# Build the harness
mvn -q -f reference-impl/pom.xml -pl legible-bench-jmh -am -DskipTests package

# In-memory suite (add -prof gc for allocation)
java -jar reference-impl/legible-bench-jmh/target/benchmarks.jar \
  -wi 3 -i 5 -f 1 -w 1s -r 1s -prof gc \
  'dev.legible.bench.jmh.(LoginThroughputBenchmark|FanOutScalingBenchmark|RegionMicroBenchmark|ConceptContentionBenchmark)'

# Postgres leg (Testcontainers; or -Dpostgres.url=... for an external DB)
java -jar reference-impl/legible-bench-jmh/target/benchmarks.jar \
  -wi 2 -i 3 -f 1 -w 1s -r 1s 'dev.legible.bench.jmh.PostgresBenchmark'

# Postgres concurrency sweep (repeat for -t 1, 4, 16 and -p mode=same|unique)
java -jar reference-impl/legible-bench-jmh/target/benchmarks.jar \
  -wi 2 -i 3 -f 1 -w 1s -r 1s -t 4 -p mode=unique \
  'dev.legible.bench.jmh.PostgresConcurrencyBenchmark.login'

# JFR profile
java -jar reference-impl/legible-bench-jmh/target/benchmarks.jar \
  -wi 1 -i 2 -f 1 -w 1s -r 1s -p followers=1000 \
  -jvmArgsAppend "-XX:StartFlightRecording=filename=/tmp/clad-fanout.jfr,settings=profile,dumponexit=true" \
  'dev.legible.bench.jmh.FanOutScalingBenchmark'
```

## Production profile summary

With the production storage profile — HikariCP + `RmapPostgresFactStore` on
PostgreSQL — the engine is **viable for moderate-throughput,
concept-partitioned workloads**, but it is not a high-throughput hot-concept
engine. Pooling was the decisive fix; what remains is SQL round-trip cost and
the engine's per-concept serialization, not connection handling.

These numbers are the engine + storage path (no HTTP transport), single-threaded
JMH on a laptop with a Testcontainers Postgres.

| Operation | Throughput | Approx. latency |
|---|---|---|
| Login flow (Hikari + Rmap) | ~1.5–1.8k flows/s | ~0.55–0.67 ms |
| `readHit` | ~13.9k ops/s | ~72 µs |
| `readMiss` | ~14.3k ops/s | ~70 µs |
| `subjects` | ~11.6k ops/s | ~86 µs |
| `write` (unbuffered primitive) | ~6.8k ops/s | ~147 µs |

For contrast: the same profile unpooled was **43 ops/s** (~23 ms/login). Hikari
is a ~40× improvement; generic fact store vs Rmap made no material difference
once pooled.

**What dominates now**

1. **Per-concept serialization.** The engine synchronizes actions per concept
   (`SyncEngine.execute`). A hot concept's ceiling is roughly
   `1 / action latency`; a login touches `UserNaming`, `PasswordAuth`, and
   `Session`, so concurrent logins contend on those concepts even with a large
   pool. This is the main scaling limit, not the pool.
2. **SQL round-trips and jOOQ overhead.** At ~72–150 µs per primitive, the
   remaining cost is execution, not borrowing a connection. That is why
   action-scoped read connections were not worth doing.
3. **Small per-action transaction overhead.** Wrapping `flushAction` in one
   transaction bought atomicity; throughput stayed within noise
   (1,484 ± 355 vs 1,823 ± 369).
4. **In-memory is a different regime.** ~256k login flows/s (~3.9 µs) in
   memory, but with scaling cliffs: `Region.subjects` and `Region.read` misses
   are full scans. Those cliffs do **not** transfer to Rmap, where the SQL index
   on `username` handles the lookup.

**What is still open**

- **HTTP transport cost** is not in these numbers; a real Micronaut request will
  be slower than a direct `app.login()` call.
- **Soak and percentile latency** under sustained load remain unmeasured; the
  concurrency sweep above is short-run (1 s iterations) and shows the plateau,
  not tail behaviour.
- **Batching / CTE update-or-insert** remains the plausible next round-trip
  reduction; the naive `ON CONFLICT` was correctly declined for the `NOT NULL`
  hazard.
- **Durable action log** is still in-memory; only concept state is durable in
  this profile.
- The roadmap's **production workload characterization** (mixed read/write,
  realistic sizes, sustained concurrency, p50/p95/p99) is still the right next
  experiment.

**Caveat.** These are hardware-relative, short-run (including the thread sweep),
Testcontainers-on-laptop figures — useful for shape and for comparing changes,
not a production capacity claim. The corrected reading of the original
"44 ops/s" is: that was the unpooled/generic baseline, not the production path.

## Capacity envelope (concurrency)

The engine treats a concept as a state machine and serializes **all** actions on
that concept (`SyncEngine.execute` uses a per-concept lock). It is not row-level
or tenant-level locking. A flow touching `UserNaming`, `PasswordAuth`, and
`Session` can overlap those three concepts, but every login contends on each of
those same locks. Adding threads helps until the hottest concept saturates, then
throughput plateaus; scaling means partitioning concepts/tenants across
processes, not adding threads to one hot concept.

`PostgresConcurrencyBenchmark` makes this reproducible: `same` hammers one user,
`unique` round-robins a pre-seeded user set. Both hit the same concept locks.

| Profile | Mode | 1 thread | 4 threads | 16 threads |
|---|---|---|---|---|
| Postgres (Hikari + Rmap) | same user | 1,518 | 2,384 | 2,372 ops/s |
| Postgres (Hikari + Rmap) | unique users | 1,509 | 2,405 | 1,885 ops/s |
| In-memory | same user | ~263k | ~460k (noisy) | ~320k (noisy) ops/s |

Two findings:

- **Unique users do not help.** Both modes plateau around ~2.4k login/s at 4
  threads; the 16-thread unique run is lower. The limit is the concept, not the
  row.
- **In-memory is a different regime.** Hundreds of thousands of simple flows/s,
  but still not thread-linear and still bounded by the hottest concept.

**Practical envelope**

- **In-memory:** embedded/tests/low-latency single-process use. Hundreds of
  thousands of simple flows/s; fan-out is linear; hot concepts cap.
- **Postgres durable:** moderate-throughput business apps — low thousands of
  login-like flows/s per process on laptop-class hardware, likely higher on
  server hardware with a native DB, but bounded by the hottest concept. Good for
  CRUD-ish, concept-partitioned domains.
- **Not a fit for:** global hot counters/queues, a single hot account,
  high-QPS fan-out, or horizontally scaling one concept. Those need partitioning,
  batching/aggregation into a concept, or a different state model.
- **Latency:** in-memory microseconds; Postgres sub-millisecond on localhost;
  real HTTP/network adds milliseconds. Soak and percentile latencies under
  sustained load remain unmeasured.

## Results

### Sequential login (in-memory)

| Harness | Throughput | Latency | Allocation |
|---|---|---|---|
| JMH `LoginThroughputBenchmark` | **256,133 ops/s** (±40,498) | ~3.9 µs/op | **17,570 B/op** |
| Hand-rolled `Bench` (same machine) | 219,306 ops/s | 4.56 µs/op | — |

The two harnesses agree on shape; JMH is slightly higher because it measures a
single hot method with a blackhole rather than a loop with a map check.

### Fan-out (social profile, N followers of the commenter)

| Followers | Throughput | Allocation |
|---|---|---|
| 1 | 220,730 ops/s | 18,178 B/op |
| 10 | 96,392 ops/s | 32,541 B/op |
| 100 | 16,566 ops/s | 205,621 B/op |
| 1000 | 1,737 ops/s | **1,909,161 B/op** |

Cost is **linear in N beyond N=10** (10× followers ≈ 6–10× lower throughput and
~10× more allocation), not quadratic. See finding 8.

### Concept contention (4 threads)

| Mode | Throughput | Allocation |
|---|---|---|
| Same user (`alice`) | 427,243 ops/s | 17,578 B/op |
| Unique user per request | 2,064 ops/s (±1,953) | 19,206 B/op |

The unique-user mode collapses because every login performs a lookup by a
non-subject field (`UserNaming.lookupByUsername` → `Region.subjects`) and the
user table grows during the run. The high variance is the run slowing as the
table grows; the absolute is not a stable throughput figure, the **trend** is
the finding.

### Region primitives (in-memory)

| Operation | 1,000 subjects | 10,000 subjects | Allocation @1k / @10k |
|---|---|---|---|
| `read` hit | 29.0M ops/s | 30.4M ops/s | 208 B / 208 B |
| `read` miss | 323,107 ops/s | 29,553 ops/s | 128 B / 128 B |
| `subjects(predicate,value)` | 95,394 ops/s | 9,835 ops/s | 6.1 KB / 56.5 KB |
| `facts()` | 21,810 ops/s | 2,314 ops/s | 39 KB / 409 KB |

`read` hit is O(1) and cheap. Every other primitive scales with the region size.

### Postgres (Testcontainers, one connection + one autocommit statement per op)

| Operation | Throughput | Approx. latency |
|---|---|---|
| Login (7-ish actions) | **44 ops/s** | ~22.7 ms |
| `read` hit | 308 ops/s | ~3.25 ms |
| `read` miss | 303 ops/s | ~3.30 ms |
| `subjects` | 296 ops/s | ~3.38 ms |
| `write` | 350 ops/s | ~2.86 ms |

Login is ~5,800× slower than in-memory. The per-operation cost (~3 ms) is
dominated by opening a connection and issuing an autocommit statement; the
engine's concept-action count multiplies it.

## Findings (ranked)

### 1. `Region.subjects` is a full region scan — highest impact

`InMemoryRegion.subjects(predicate, value)` iterates every subject
(`InMemoryFactStore.java`). Any concept that looks up by a non-subject field —
username, email, tag, follower target — pays O(individuals) per lookup. This is
the direct cause of the `unique` contention collapse and the O(N) fan-out
adjacency cost.

- Evidence: `RegionMicroBenchmark.subjects` falls 95k → 9.8k ops/s as subjects
  go 1k → 10k; `ConceptContentionBenchmark` unique-user mode degrades as the
  table grows.
- Candidate: maintain a `predicate → value → subjects` reverse index in
  `InMemoryRegion` (and add the matching SQL index for Postgres). Expected
  impact: turns the dominant scaling term from O(region) to O(matches).

### 2. `Region.read` on a miss scans the whole region

The composite-subject fallback in `InMemoryRegion.read` scans every entry when
the exact subject key is absent. A plain miss (an `OPTIONAL`/`absent` read for
data that is not there) pays O(region).

- Evidence: `readMiss` 323k → 29.6k ops/s from 1k → 10k subjects.
- Candidate: distinguish composite-key reads structurally (a composite index or
  a sorted-key range scan) instead of a prefix scan on every miss.

### 3. Postgres connection-per-operation dominates the durable profile

`PostgresFactStore.PgRegion` calls `dataSource.getConnection()` for every read
and every write, with no pooling, batching, or per-action transaction.

- Evidence: 44 ops/s login; every primitive ~3 ms.
- Candidates (each measurable): connection pool (e.g. HikariCP), one
  transaction per concept action, batched writes, and indexes for
  `subjects(predicate,value)` / `facts()` (the current PK starts with
  `concept`, so those predicates cannot use it efficiently).

### 4. Per-action allocation is high; frame-map copies dominate fan-out

Login allocates ~17.6 KB/op; fan-out allocates ~1.9 KB **per follower** per
comment. JFR attributes 33% of fan-out allocation to `LinkedHashMap$Entry`,
15% to `HashMap$Node[]`, 11% to `LinkedHashMap`, 14% to `byte[]`, and 6% to a
`SyncEngine` lambda.

- Sources: `WhereEvaluator` copies the whole frame map per fan-out row;
  `SyncEngine.processInvocation` copies the output map per action; `then.args`
  builds a fresh `LinkedHashMap` per invocation.
- Candidate: avoid the frame copy when a clause does not fan out; project
  `then` args without an intermediate map; reuse per-flow buffers where safe.
  This is allocation pressure, not a correctness change.

### 5. `UUID.randomUUID` per action and per flow is a measurable cost

JFR shows `SecureRandom`/`NativePRNG` at ~13–19% of samples in both end-to-end
benchmarks. `SyncEngine.run` and `mint`/`processInvocation` call
`UUID.randomUUID()` for flow and action ids.

- Candidate: use a non-crypto monotonic id generator for opaque action/flow ids
  (they are internal lineage tokens), keeping UUIDs only where an external
  contract requires them. This is a behaviour-preserving substitution if the
  id is treated as opaque.

### 6. Flow-log lookups are linear scans (low/medium today)

`InMemoryActionLog.invocations(flowId)`, `completionByFlowAction`, and
`hasEmission` scan the flow log; `SyncEngine.matchConjuncts` calls them per
candidate rule. Measured at ~3–5% of login samples and ~2% of fan-out samples.

- Candidate: index invocations by `(concept, action)` and emissions by
  `(parentActionId, syncName)` within the per-flow log. Low urgency at current
  flow lengths; grows with long chains.

### 7. Per-request archival is included in end-to-end cost

`FlowArchiver.archive` scans and copies the flow twice plus a synchronized
buffer add. Not separately isolated in this pass; it is part of the 17.6 KB/op
login allocation.

- Candidate: single-pass extraction and a non-copying buffer add; measure
  before changing.

### 8. Refuted: fan-out is not O(N²) in the tested shape

The static read suspected O(N²) from per-completion log scans. The measured
fan-out curve is linear in N beyond N=10. Follower `notify` completions match no
rules, so `matchConjuncts` does not run per follower; the cost is frame
multiplication, per-follower writes, and allocation. The suspected quadratic is
**not** present for this shape.

## Prioritised candidates

| Priority | Candidate | Expected impact | Effort | Risk | Route |
|---|---|---|---|---|---|
| P0 | Reverse index for `Region.subjects` | Removes the dominant in-memory scaling term | M | Medium (index consistency) | R20 platform |
| P0 | Fix `Region.read` miss scan | Removes O(region) optional reads | M | Medium (composite-key semantics) | R20 platform |
| P1 | Postgres pooling + per-action transaction/batch + indexes | Order-of-magnitude durable gain | M–L | Medium (transaction semantics) | R20 platform |
| P1 | Reduce frame/`then`/output map copies | Lower GC pressure, higher fan-out throughput | M | Low (allocation only) | R20 platform |
| P2 | Faster opaque id generation | Removes ~13–19% SecureRandom cost | S | Low (id format) | R20 platform |
| P2 | Flow-log indexes | Long-chain headroom | S–M | Low | R20 platform |

None is applied in this pass. Each needs its own maintenance record and design
gate, plus before/after measurements on the same harness.

## Caveats

- **Hardware-relative.** One laptop-class machine, JDK 25, one session.
- **Testcontainers overhead.** The Postgres numbers include Docker Desktop
  networking and container startup amortised over the run; a native Postgres or
  a pooled client would be faster. The *shape* (per-op connection cost) is the
  finding, not the absolute.
- **Unique-user contention.** The workload intentionally grows the user table;
  the high variance is real degradation, not JMH noise. A fixed pre-seeded user
  set would give a stable absolute but would hide the scan finding.
- **Not a production workload.** No mixed read/write mix, no realistic graph
  sizes, no soak/GC-under-sustained-load. The roadmap's production
  characterisation remains open.

## Addendum — 2026-11-09 (pooled baseline)

The original Postgres leg used an unpooled `PGSimpleDataSource` and the generic
`PostgresFactStore`. That is not the production path: `java-micronaut` already
uses `micronaut-jdbc-hikari` + `RmapPostgresFactStore`, and `java-plain` was the
unpooled profile. `PostgresBenchmark` now parameterises `pool=simple|hikari` and
`store=generic|rmap`, so the two effects are separated.

Login throughput (JDK 25, Postgres 16 via Testcontainers, JMH):

| Pool | Store | Login ops/s |
|---|---|---|
| simple | generic | 43.0 |
| simple | rmap | 43.5 |
| hikari | generic | 1,781.7 |
| hikari | rmap | 1,822.8 |

Rmap primitives, simple → hikari: `readHit` 312 → 13,934; `readMiss` 306 →
14,259; `subjects` 318 → 11,608; `write` 164 → 6,809 ops/s.

**Corrected reading:** pooling is the dominant lever (~40×); the generic vs Rmap
choice makes no material difference once pooled. The remaining ~70–150 µs per
primitive is SQL round-trip plus `RmapRegion`'s `fetchCount` + update/insert,
which the `rmap-upsert-transaction` change targets. The earlier "44 ops/s"
figure should be read as the unpooled/generic baseline, not the production
bottleneck.

### Addendum — Phase 2 (per-action transaction)

`RmapRegion.flushAction` now wraps all buffered rows of one concept action in a
single `dsl.transaction(...)`, so the action commits or rolls back as one unit.

- Login (hikari/rmap): 1,484 ± 355 ops/s vs 1,823 ± 369 before — inside the
  error bars at this sample size. The transaction buys atomicity, not throughput.
- **Declined:** replacing `fetchCount` + update/insert with
  `INSERT … ON CONFLICT DO UPDATE`. PostgreSQL validates `NOT NULL` on the
  proposed insert tuple before conflict resolution, so a partial upsert of an
  existing multi-column row would be rejected for an absent mandatory sibling
  (`RmapPostgresFactStore.java:749-757`). Update-then-insert stays.
- **Phase 3 not triggered:** with Hikari, `readHit` is ~72 µs/op and a pool
  borrow is a few µs, so action-scoped read connections would not move the
  needle. The remaining cost is SQL/jOOQ execution, not connection acquisition.

### Addendum — 2026-11-09 (per-subject locking, B)

Step 0 (`ConceptTimingProbe`) attributed the login flow on Hikari/Rmap: the
`PasswordAuth` concept lock was ~0.99 of wall at 4 threads (`check` action +
flush), and `same` vs `unique` users both plateaued at ~2.3k login/s. That
identified the per-concept lock as the ceiling.

The `per-subject-concept-locking` change replaces the per-concept lock with
striped locks keyed by a declared subject, makes `RmapRegion`'s action buffer
thread-local, and declares subject keys on the example concepts (`Web` is
stateless). A throwaway lab app (`dev.legible.bench.concurrency`) tests the
strategy: a hot counter, unique accounts, and multi-subject transfers.

Lab results (Hikari/Rmap; correctness all PASS):

| Workload | 1 thread | 4 threads |
|---|---|---|
| Counter, same subject | 2,318/s | 2,859/s |
| Counter, unique subjects | 2,443/s | 7,517/s |
| Accounts, unique | 2,584/s | 8,194/s |
| Transfer, multi-subject | 1,574/s | 4,618/s |

Login JMH (`PostgresConcurrencyBenchmark`), before → after:

| Mode | 1 thread | 4 threads |
|---|---|---|
| same user | 1,518 → 1,298 | 2,384 → 2,134 |
| unique users | 1,509 → 1,347 | 2,405 → 3,596 |

**Reading:** per-subject locking works — unique subjects scale ~3× in the lab,
the same subject stays flat, and multi-subject transfers scale without deadlock.
The login flow gains ~50% for unique users because its next bottleneck is DB
flush/round-trip cost, not the lock: at 4 threads `PasswordAuth/flushAction` and
`Session/flushAction` utilisation exceeds 1.0. The next lever is round-trip
reduction (CTE/batching), not more locking.
