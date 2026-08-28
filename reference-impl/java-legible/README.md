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

`dev.legible.bench` (in the scratch prototype) measured the engine against
the Jena profile's own concurrency harness: ~3 µs/request sequential, ~100×
lower latency and ~50× higher throughput under concurrency, with no errors.
