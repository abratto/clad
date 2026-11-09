<!-- Maintenance-route planning record. -->
# Maintenance change — `postgres-hikari-pool`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `active` (`draft` until design approval, `active` while implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-bench-jmh`, `reference-impl/java-plain`, `reference-impl/java-micronaut`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Correct the Postgres performance baseline (pool + store matrix, including `RmapPostgresFactStore`), then replace `java-plain`'s unpooled `PGSimpleDataSource` with a HikariCP-backed `AutoCloseable` runtime and make the Micronaut pool settings explicit.
- **Dependent re-entry:** `none`

## Why

The 2026-11-09 review measured Postgres at 44 ops/s login using an
**unpooled** `PGSimpleDataSource` and the **generic** `PostgresFactStore`
(`docs/experiments/engine-performance-review.md`). That is not the production
path: `java-micronaut` already depends on `micronaut-jdbc-hikari` and binds
`RmapPostgresFactStore`, while `java-plain` boots an unpooled
`PGSimpleDataSource` (`PlainPostgresApp.boot`). The baseline must separate
pooling from store choice before any optimisation is judged.

## Mechanism

- **Phase 0 (measurement):** `PostgresBenchmark` gains
  `@Param pool=simple|hikari` and `@Param store=generic|rmap`. The Rmap arm
  constructs `RmapPostgresFactStore(dataSource, LoginSchemas.all())` and calls
  the dev/test `createSchema()` helper. This isolates the connection-pool gain
  from the store choice.
- **Phase 1 (java-plain):** `PlainPostgresApp.boot()` returns an
  `AutoCloseable` `Runtime` holding a `HikariDataSource` and the `LoginApp`.
  HikariCP 6.3.3 is BOM-managed by `micronaut-platform`; the pool uses
  `jdbcUrl` (not `url`), the existing `DATABASE_URL`/`PGUSER`/`PGPASSWORD`
  environment variables, `PGPOOL_MAX` (default 10), and `poolName=clad-plain`.
  Flyway migrates on the pooled `DataSource`; `Runtime.close()` closes the pool
  idempotently.
- **Phase 1 (micronaut):** `application.yml` states the Hikari pool settings
  explicitly instead of relying on framework defaults.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Pooling and boot lifecycle only; no concept/sync/outcome change |
| Action ordering and sync deduplication | `preserved` | No engine change |
| Flow-token lineage | `preserved` | No engine change |
| Storage/retention semantics | `preserved` | Same `FactStore` SPI and schema; only connection acquisition changes |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `docs/experiments/engine-performance-review.md`, `java-plain/README.md`, `reference-impl/README.md` |
| Profile configuration or deployment files | yes | `java-plain/pom.xml` (+HikariCP), `legible-bench-jmh/pom.xml`, `java-micronaut/src/main/resources/application.yml` |
| Engine/runtime implementation | no | No `legible-engine` change; `java-plain` boot wiring only |
| Profile tests | yes | `PlainPostgresAppBootTest` moves to the `Runtime` handle; JMH Postgres matrix |
| UC artefact chain | no | No outcome, contract, sync, or ordering change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Postgres baseline matrix recorded | bench | `PostgresBenchmark` login across pool/store combinations | pass | 43/43.5/1782/1823 ops/s for simple-generic/simple-rmap/hikari-generic/hikari-rmap |
| Rmap store measured under both pools | bench | `PostgresBenchmark` `-p store=rmap` primitives | pass | readHit 312→13.9k, readMiss 306→14.3k, subjects 318→11.6k, write 164→6.8k ops/s |
| `java-plain` boots on Hikari and closes deterministically | integration | `mvn -f reference-impl/pom.xml -pl java-plain test -Dclad.storage=postgres` | pass | 1 test, Hikari pool boot + `close()` shuts it down |
| Micronaut profile still green | integration | `mvn -f reference-impl/pom.xml -pl java-micronaut test` | pass | 20 tests, 0 failures (4 Postgres-gated skips) |
| No engine source change | gate | `git diff --stat` | pass | only harness/pom/profile/docs changes |
| Artefact gate stays green | integration | `python3 quality-gate/verify_artefacts.py` | pass | exit 0, pipeline intact |

## Evidence — Phase 0

2026-11-09, JDK 25.0.2, Postgres 16 via Testcontainers, JMH 1.37. Login
throughput across the pool/store matrix:

| Pool | Store | Login ops/s |
|---|---|---|
| simple | generic | 43.0 |
| simple | rmap | 43.5 |
| hikari | generic | 1,781.7 |
| hikari | rmap | 1,822.8 |

Rmap primitives, simple → hikari: `readHit` 312 → 13,934; `readMiss` 306 →
14,259; `subjects` 318 → 11,608; `write` 164 → 6,809 ops/s.

**Reading:** pooling is the dominant lever (~40×); generic vs Rmap makes no
material difference once pooled. The remaining ~70–150 µs per primitive is SQL
round-trip and `RmapRegion`'s `fetchCount` + update/insert, which the separate
`rmap-upsert-transaction` change targets.

## Evidence — Phase 1

- `PlainPostgresApp.boot()` now returns an `AutoCloseable Runtime` owning a
  `HikariDataSource` (`PGPOOL_MAX` default 10, `PGPOOL_MIN_IDLE` default 2).
  `main()`, the README, and `PlainPostgresAppBootTest` use try-with-resources;
  the test asserts the pool is closed after `close()` and that the DataSource is
  a `HikariDataSource`.
- `java-micronaut/application.yml` states the pool settings explicitly
  (`maximum-pool-size`, `minimum-idle`, `connection-timeout`, `pool-name`).
- Tests: `java-plain` 1/1 (Docker-backed), `java-micronaut` 20 tests, 0
  failures (4 Postgres-gated skips). Artefact gate green.
- No engine or storage source changed in this phase.

## Gates

### Design gate

The human reviews scope, the `AutoCloseable` `Runtime` API break, the HikariCP
choice (6.3.3, BOM-managed), and the test matrix. Approve with
`./clad approve-maintenance postgres-hikari-pool design`, then set Status to
`active`.

### Evidence gate

The human reviews the Phase 0 matrix, the `java-plain`/Micronaut test results,
and the before/after numbers. Approve with
`./clad approve-maintenance postgres-hikari-pool evidence`, then set Status to
`closed`.

## Notes

- **Non-goal:** round-trip reduction in `RmapPostgresFactStore` — that is the
  separate `rmap-upsert-transaction` change.
- **API break:** `PlainPostgresApp.boot()` returns `Runtime` instead of
  `LoginApp`; `main()`, the boot test, and the README are updated.
- **Rollback:** revert the boot wiring and pom dependency; no schema or
  contract change.
