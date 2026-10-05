# Maintenance change — `java-plain-profile`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** new `reference-impl/java-plain` (plus root
  `reference-impl/pom.xml` module list, CI workflow, pointers); reuses
  `legible-engine`, `legible-storage`, `java-legible` unchanged
- **Feature-contract impact:** `preserved` (no use-case outcome, response,
  flow-token, or derived-schema change — the same login trio and the same
  `LoginSchemas` derivation source)
- **Design gate:** `approved` (human, in-conversation: "Let's do option A" —
  ship a bootable plain-Java + Postgres profile, no HTTP transport, so an app
  may bring any framework or none)
- **Evidence gate:** `approved`
- **Change summary:** Add `reference-impl/java-plain`: a runnable plain-Java
  profile over the durable stack — a `PlainPostgresApp` (env-configured
  `DataSource` → Flyway migrate → `RmapPostgresFactStore(LoginSchemas.all())`
  → `LoginApp.create(store)` → scripted flow in `main()`), its own
  byte-identical `V1` migration with the same drift-guard test, and a
  Docker-gated boot test. No new code in engine/storage; the Micronaut
  coupling of the durable stack stays confined to `java-micronaut`.

## Mechanism

- The durable stack is already framework-free — `legible-storage` has zero
  Micronaut imports and depends only on the PG driver and jOOQ; the profile is
  therefore pure assembly. `PlainPostgresApp` composes it directly:
  `PGSimpleDataSource` from `DATABASE_URL`/`PGUSER`/`PGPASSWORD` (defaults
  mirroring `java-micronaut/application.yml`), `Flyway.configure()…migrate()`
  before any store use (the migration-before-store invariant the profile's
  own `StoreInitializer` encodes), then `new RmapPostgresFactStore(dataSource,
  LoginSchemas.all())` and `LoginApp.create(store)`.
- Flyway owns DDL exactly as doctrine requires: the profile commits its own
  `V1__login_rmap.sql` (the same bytes `java-micronaut` carries — both render
  `RmapMigration.renderModels` over `LoginSchemas.all()`), and
  `RmapMigrationTest` (same name, same `rmap.migration.write` regeneration
  switch) fails on drift.
- No HTTP: `main()` runs the seeded login scenario end to end (OK / bad
  password / lockout) through the engine's `LoginApp.login`, printing the
  Web.respond payload — demonstrating that transport is pluggable by absence.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | `LoginApp` outcomes and messages identical; no new concept/sync code. |
| Action ordering and sync deduplication | `preserved` | No engine change. |
| Flow-token lineage | `preserved` | Flow log untouched. |
| Storage/retention semantics | `preserved` | Same `RmapPostgresFactStore` + Flyway-owned `V1` (byte-identical migration). |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | New module README; `RELATIONAL_RMAP.md` bindings row; `reference-impl/README.md` list. |
| Profile configuration or deployment files | no | No config keys changed; no Dockerfile needed (no transport). |
| Engine/runtime implementation | yes | New module only: root pom lists it; modules it depends on are untouched. |
| Profile tests | yes | New: boot test (Docker-gated), migration drift test. |
| UC artefact chain | no | Derives from the same 03b machine-model files. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Flyway owns the schema before the store; login round-trip over the plain stack | integration (Testcontainers) | `PlainPostgresAppBootTest` | pass | boot → history has V1 → 200+sessionToken → 401 bad → lockout message, all no-HTTP |
| Profile migration ≡ `LoginSchemas` derivation (no drift) | drift | `RmapMigrationTest` (module-local) | pass | regenerated once with the profile's own label; bytes equal `java-micronaut`'s V1 apart from the header label |
| Reactor stays green (Docker-free) | gate | full reactor without Docker | pass | 41/47/66/21(4 skip)/2(1 skip) — plain: drift guard runs, boot test skips |
| CI parity with the durable profile | CI | `postgres-verify` job includes `java-plain` | pass | workflow: `-pl legible-storage,java-micronaut,java-plain -am -Dclad.storage=postgres` |

## Gates

### Design gate

Approved in-conversation (2026-10-05): Option A — a real `java-plain`
profile rather than a bootstrap helper, keeping derived-repo freedom of HTTP
framework; self-contained Flyway V1 with its own drift test; same
`clad.storage` gating so the Docker CI jobs pick it up unchanged.

### Evidence gate

Approved — matrix above: postgres reactor 41/47/66/21/2 BUILD SUCCESS
(`PlainPostgresAppBootTest` + module drift guard run under `-Dclad.storage=postgres`),
Docker-free full reactor green (drift guard runs, boot test skips), live
`main()` round-trip against a throwaway container (200 + sessionToken / 401),
test.command exit 0, pytest 313 passed.

## Notes

- Compatibility: no existing module changes beyond the root pom's module
  list and CI workflow; `java-micronaut` remains the adapter-owning profile.
- A Dockerfile/compose for java-plain is out of scope intentionally — the
  profile's point is that deployment transport is the adopter's choice; the
  micronaut profile keeps the shipped smoke path.
- Rollback: drop the module from the root pom list; nothing else is coupled.
