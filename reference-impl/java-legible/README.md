# java-legible

The canonical in-memory reference profile on the fire-after-commit engine.

## Contents

- **UC-00-login** (`dev.legible.example.login`) — the worked example,
  re-lowered from the legacy engine: `Web` (request/respond), `UserNaming`,
  `PasswordAuth`, `Session`, and the seven `SyncRule`s. `FlowTraceTest`
  asserts the runtime flow-token chain matches the chain table; `LoginFlowTest`
  asserts the four scenarios.
- **Example features** exercising the sync model the login feature does not:
  - `social` — fan-out, Pattern D concept-state reads, multi-target `then`.
  - `tagging` — `OPTIONAL` reads and `?_eachthen` aggregation.
  - `token` — `bind(uuid())` in a sync's `where` clause.
- **Engine tests** — `WhereEvaluatorTest` (matcher), `EngineSemanticsTest`
  (fire-after-commit, replay, archival, route scoping), `DebugApiTest`.

## Running

```bash
mvn test -f reference-impl/pom.xml -pl java-legible -am
```

## Performance

Hand-rolled benchmarks ship in the reactor under
[`../legible-bench/`](../legible-bench/) — run them (advisory, not CI):

```bash
mvn exec:java -f reference-impl/pom.xml -pl legible-bench -am \
    -Dexec.mainClass=dev.legible.bench.Bench              # sequential
mvn exec:java -f reference-impl/pom.xml -pl legible-bench -am \
    -Dexec.mainClass=dev.legible.bench.ConcurrencyBench   # unique-user sweep
mvn exec:java -f reference-impl/pom.xml -pl legible-bench -am \
    -Dexec.mainClass=dev.legible.bench.FanOutBench        # fan-out vs follower count
mvn exec:java -f reference-impl/pom.xml -pl legible-bench -am \
    -Dexec.mainClass=dev.legible.bench.SerializationBench # same-user ceiling
```

Numbers below are one session on a 2026 laptop-class machine (JDK 25) and are
hardware-relative — treat shape, not absolutes, as the finding:

| Benchmark | Result |
|---|---|
| Sequential (100k login flows) | ~5.3 µs/request, ~190k ops/s, zero in-flight flow leaks |
| Concurrency, unique user (levels 1–32) | peaks ~18k req/s at 4 threads, degrades to ~3.3k at 32; every request seeds its own user, so per-request state writes serialize on concept locks |
| Same-user hot-contention ceiling | throughput *rises* to ~54k req/s at 64 threads (no per-request seeding); max sustainable actions/sec per hot concept ≈ 1 / avg action latency |
| Fan-out (social, N followers of commenter) | N=1 ~17–21k req/s; N=100 ~3–5.6k req/s; N=1000 ~406–767 req/s — cost scales roughly linearly with N (frame multiplication × per-follower notify actions) |

See `../../maintenance/engine-benchmark.md` for methodology and the record.
