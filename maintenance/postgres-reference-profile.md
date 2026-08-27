# Maintenance change — `postgres-reference-profile`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/java-micronaut-postgres` (new); methodology docs (`STORAGE_MAPPING.md`, `clad.properties`, `templates/`)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Add a `java-micronaut-postgres` reference profile that keeps the shared in-memory action log unchanged but persists concept state relationally in Postgres via JOOQ + Flyway, using a deterministic Rmap (ORM→relational) lowering.

## Why

The action log is profile-agnostic (always in-memory Jena) and now lives in the
shared `clad-engine` module. Concept-state persistence is the one per-profile
surface. The Jena profile realises it as RDF named graphs; this change adds a
second, relational realisation so projects that want a SQL/Postgres concept
store can adopt CLAD without re-deriving the lowering by hand.

The lowering is not ad hoc: CLAD's Stage 03b data model is a CSDP fact model
(Halpin's ORM tradition), so its relational mapping is the deterministic
Halpin Rmap — specialised here for CLAD's state notation and its no-cross-concept
rule. Documenting that as `RELATIONAL_LOWERING.md` makes Stage 04a mechanical and
reviewable, the relational analog of `SYNC_LOWERING.md`.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Same `Web/respond` contract, same syncs; only concept-state storage changes |
| Action ordering and sync deduplication | preserved | Syncs and the dispatch loop are unchanged (shared `clad-engine`) |
| Flow-token lineage | preserved | `FlowManager`/`FlowArchiver` unchanged; action log still in-memory Jena |
| Storage/retention semantics | changed | Concept state moves from named graphs to a Postgres schema per application. Deliberate, profile-scoped — no re-entry (concept/sync/spec slices unchanged) |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | New profile `README.md`/`CODE_STYLE.md`/`CANONICAL_EXEMPLAR.md` + `RELATIONAL_LOWERING.md`; `STORAGE_MAPPING.md` §Relational; `reference-impl/README.md` module list |
| Profile configuration or deployment files | yes | `clad.properties` (`storage.layer` example, `test.command` unchanged); new profile `pom.xml`, `application.yml`, Flyway migrations |
| Engine/runtime implementation | no | `clad-engine` and `java-micronaut-jena` are untouched by this change |
| Profile tests | yes | New profile's concept/flow/ArchUnit tests (Testcontainers Postgres); `verify_relational_mapping.py` + its test |
| UC artefact chain | no | No concept/sync/spec slice changes; stage sequence unchanged |

## Design

### Reactor addition

```
reference-impl/
├── pom.xml                      (add <module>java-micronaut-postgres</module>)
├── clad-engine/                 (unchanged)
├── java-micronaut-jena/         (unchanged)
└── java-micronaut-postgres/     (NEW)
    ├── pom.xml
    ├── RELATIONAL_LOWERING.md
    ├── CODE_STYLE.md / README.md / CANONICAL_EXEMPLAR.md
    └── src/main/
        ├── resources/db/migration/V{n}__<concept>__<table>.sql
        ├── resources/application.yml
        └── java/com/example/app/
            ├── Application.java          (bootstrap + DemoSeed, copied)
            ├── api/                      (DTOs + ResponseAssembler, copied)
            ├── infrastructure/           (controllers, copied)
            ├── syncs/                    (7 syncs, copied verbatim)
            ├── concepts/{user,passwordauth,session}/   (JOOQ state — NEW)
            └── storage/JooqFactory.java  (ActionLog + DataSource + DSLContext — NEW)
```

The `syncs`, `infrastructure`, `api`, and `Application` are copied verbatim from
the Jena profile (they are transport/coordination code that never touches
concept state). Only the `concepts` package and the `storage` wiring differ.

### Concept state — JOOQ + Flyway, schema-per-application + prefix

Application schema `public`; each table's name carries its owning concept.

```sql
CREATE TABLE user_accounts (            -- user: username: UserId -> String
    user_id   uuid PRIMARY KEY,
    username  text NOT NULL UNIQUE
);
CREATE TABLE passwordauth_credentials ( -- passwordauth: passwordHash/failedAttempts/lockedUntil
    user_id        uuid PRIMARY KEY,    -- opaque cross-concept id, NO FK
    password_hash  text NOT NULL,
    failed_attempts int  NOT NULL DEFAULT 0,
    locked_until   timestamptz NULL
);
CREATE TABLE session_tokens (           -- session: token -> userId
    session_token uuid PRIMARY KEY,
    user_id       uuid NOT NULL         -- opaque, NO FK
);
```

Rules: one owning concept per table (prefix); no FK crosses a concept boundary;
mandatory → `NOT NULL`, optional → nullable, default → `DEFAULT`.

### `RELATIONAL_LOWERING.md` — the Rmap rule set

Maps CLAD's Stage 03b state forms deterministically (Halpin Rmap specialised):

| 03b form | Realization |
|---|---|
| `field: S -> V` (mandatory) | column on S's table, `NOT NULL` |
| `field: S -> V` (optional) | column on S's table, nullable |
| `List<T>` / `Map<K,V>` / "zero or more" | child table, composite PK, intra-concept FK |
| nested struct / objectified fact | separate table, surrogate/composite key |
| value constraint | `CHECK` |
| intra-concept entity reference | real FK |
| **cross-concept identifier** | opaque typed column, never a FK |

### Codegen + runtime

- **Flyway** migrations in `src/main/resources/db/migration/`, run at startup
  against the configured `DataSource` (HikariCP via `micronaut-jdbc-hikari`).
- **JOOQ codegen** uses `DDLDatabase` to parse the Flyway `.sql` files offline
  (no live DB at build); generated records under `com.example.app.db`.
- **`JooqFactory`** provides the `ActionLog` bean (in-memory `LocalStorage` +
  `FlowArchiver`, no business-graph routing) and the `DSLContext` bean.
- **`PasswordAuth.doCheck`** mirrors the Jena profile's read-modify-write
  semantics; JOOQ makes an atomic `UPDATE … RETURNING` available if a project
  wants to close the counter race (documented, not enabled by default).

### Enforcement

- **`verify_relational_mapping.py`** (new, conditional, wired into Stage 04a via
  `clad_stages.py`): skips features with no relational Stage 04a mapping; for
  relational mappings it rejects any `REFERENCES`/`FOREIGN KEY` (cross-concept FK
  is forbidden by R2). Deeper nullability/fact-type-realization checks are
  specified in `RELATIONAL_LOWERING.md` and reviewed by the human at Stage 04a.
- **ArchUnit** (profile-local `LegibleArchitectureRulesTest`): R1/R3/R4/R5
  unchanged; R2 adapted to "no concept accesses a sibling concept's JOOQ table"
  (prefix-ownership check over the generated `com.example.app.db.tables`).

### Non-goals

- No change to `clad-engine`, `java-micronaut-jena`, the action log, syncs,
  `advance.py`, or the stage sequence.
- No ORM/JPA (rejects the object trap `verify_concept_state_relational.py` gates).
- No RLS/per-role hardening in the default profile.
- No change to the Jena profile's tests or docs (only `reference-impl/README.md`
  module list and the methodology docs noted above).

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Concept state round-trips through Postgres | unit/integration | `UserLookupByUsernameTest` (2), `PasswordAuthCheckTest` (3), `SessionGrantTest` (1) — Testcontainers | pass | 6/6 green |
| Full login flow resolves (200/401) on Postgres state | flow-regression | `LoginFlowTest` (2) — `@MicronautTest` + Testcontainers | pass | 200 + 401 |
| No cross-concept table access | unit | `LegibleArchitectureRulesTest.r2_no_cross_concept_table_access` (+R1/R3/R4/R5) | pass | 5/5 green |
| Relational mapping gate | unit | `verify_relational_mapping.py` + `quality-gate/tests/test_relational_mapping.py` | pass | 5/5 green |
| Rmap gate skips non-relational profiles | unit | `verify_artefacts.py` over UC-00-login (RDF) — Stage 04a check skips | pass | artefact gate PASS |
| Full regression | integration | `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml` | pass | 91 tests 0 failures (3 modules) |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before any
implementation. Approve with `./clad approve-maintenance postgres-reference-profile design`,
then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- **Cross-repo compatibility (clad-agent):** no change to `advance.py`, the stage
  sequence, `templates/feature-skeleton`, or any bundled knowledge file, so
  clad-agent is unaffected. The `storage.layer` example change in `clad.properties`
  is doc-only (clad-agent reads `_config/build-and-test.md`, not `clad.properties`).
- **`test.command`** stays `mvn test -f reference-impl/pom.xml` (the reactor now
  builds three modules; the Jena profile's tests remain green).
- **JOOQ codegen is offline** (`DDLDatabase` over Flyway SQL), so `mvn test` and
  CI need no live database; only the Testcontainers-backed tests spin up Postgres.
- **Coupling-gate refinement:** the new profile re-realizes the already-approved
  UC-00-login concepts/syncs, which `verify_iterative_change_coupling.py` would
  otherwise flag as spec-decoupled. The gate now defers to an active maintenance
  record (R20 governs platform maintenance; R17 governs iterative drift).
