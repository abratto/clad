# Maintenance change — `factstore-profile-ports`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `mixed`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`, `reference-impl/java-micronaut-postgres`, `reference-impl/java-legible` (test wiring)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Land `JenaFactStore` and `PostgresFactStore` implementations of the `FactStore`/`Region` SPI so the fire-after-commit engine provably runs against Jena and Postgres storage (not only in-memory), plus re-target the implementation-parity scripts to the `SyncRule`/`Concept` shape.

## Why

`maintenance/fire-after-commit-engine.md` landed the fire-after-commit engine
with `InMemoryFactStore` as the only backend, deferring the Jena/Postgres ports
("port both" — a decision already made at that change's design gate). Until those
ports exist, the "storage-agnostic engine" claim is demonstrated only in memory,
and the parity scripts still only understand the legacy `SyncAgent`/`ConceptAgent`
shape — so the new engine's syncs/concepts are not mechanically parity-checked
against their specs.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | The same `Concept`/`SyncRule` code runs against every backend; the login flow returns identical status/fields |
| Action ordering and sync deduplication | preserved | Engine semantics are storage-independent (the log is in-memory per flow) |
| Flow-token lineage | preserved | Unchanged — provenance lives in the action log, not the fact store |
| Storage/retention semantics | changed | Adds Jena (named graph per concept) and Postgres (relation table per concept) backends behind the same `FactStore` SPI; in-memory remains canonical |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `reference-impl/java-micronaut-jena/README.md`, `CODE_STYLE.md`/`RELATIONAL_LOWERING.md` notes on the `FactStore` boundary |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `JenaFactStore` (jena profile), `PostgresFactStore` (postgres profile) — new `FactStore`/`Region` implementations |
| Profile tests | yes | login-flow tests against each backend; `FactStore` SPI tests |
| UC artefact chain | no | specs unchanged — this is storage-mapping (04a) at the profile level, not a feature re-entry |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| JenaFactStore SPI | unit | read/write/remove/clear/subjects/facts over a Jena Dataset | pass | `JenaFactStoreTest` (8 tests green) |
| PostgresFactStore SPI | integration | same, over a Testcontainers Postgres | pass | `PostgresFactStoreTest` (8 tests green) |
| Login flow parity across backends | flow-regression | `StorageContractTest` login scenarios against Jena + Postgres | pass | 16 tests green (identical outcomes/fields) |
| Parity scripts understand SyncRule/Concept | unit | `verify_implementation_parity.py`/`verify_sync_implementation_parity.py` against java-legible | pass | 11 impl classes / 7 syncs, backward-compatible with Jena (10 classes) |
| Full regression | integration | `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml` | pass | BUILD SUCCESS, 6 modules |

## Gates

### Design gate

Approve with `./clad approve-maintenance factstore-profile-ports design`, then set Status to `active`.

### Evidence gate

Approve with `./clad approve-maintenance factstore-profile-ports evidence` after the test matrix is green.

## Notes

- This is the deferred half of `fire-after-commit-engine.md` ("port both to FactStore").
- The parity-script re-targeting lives in `quality-gate/` (not maintenance scope) but is
  bundled here because it is the mechanical counterpart of the new code shape.
- `PostgresFactStore` tests require Docker (Testcontainers).
- **Documentation follow-up:** the concept-naming refinement (name the capability,
  not the entity) and the relational-state principle (state over a set, not fields
  of an object) were carried into the engine's `Concept`/`Region` javadoc and
  `STORAGE_MAPPING.md`, so implementation and persistence generation reflect the
  same guidance the spec template (`templates/concept.md`) already enforced.
- **Rmap realization:** `RmapPostgresFactStore` adds the deterministic, typed,
  keyed, constrained relational schema (relation realization via Halpin's Rmap)
  behind the same `FactStore` SPI, alongside the generic `PostgresFactStore`
  (fact realization). `LoginSchemas` derives the UC-00-login tables from the
  Stage 03b data models.
