# Maintenance change — `micronaut-transport-storage-split`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** new `reference-impl/java-micronaut`; `reference-impl/java-micronaut-postgres` (becomes the Postgres binding); reactor `pom.xml`; docs
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Separate the Micronaut HTTP **transport** from the **storage backend** so the same service runs over in-memory, Postgres, or a backend you provide, selected by configuration rather than by choosing a fused module. Today `java-micronaut-postgres` hard-wires `RmapPostgresFactStore` (Flyway/jOOQ/Postgres deps, `StoreInitializer`, R-map schemas) into the only Micronaut profile.

## Why

The reference-profile guidance now states that transport and storage are
independent concerns over the `FactStore` SPI — but the code does not honour
that: the only Micronaut profile is inseparable from Postgres. A user who wants
"a Micronaut backend with in-memory state" (dev/test, or a service whose
durability is decided later) has no starting point, and the profile name
conflates two axes. Surfaced while documenting "Choosing a reference profile".

## Design question (the gate's subject)

Two viable factorings:

**Option A — two modules.** `java-micronaut` = Micronaut transport + in-memory
`FactStore` + the login concepts/syncs/controllers; `java-micronaut-postgres` =
the same app with a Postgres `FactStore` binding. Duplicates the transport layer
or requires a shared base module.

**Option B — one Micronaut module, two storage bindings selected by
configuration** (proposed). One `java-micronaut` module holds the transport,
concepts, syncs, and controllers plus **two** `FactStore` `@Factory` bindings
(in-memory and Postgres) behind a `clad.storage` config key; Micronaut's
`@Requires`/`@Named` picks one. Postgres-only resources (Flyway migration,
`StoreInitializer`, R-map schemas, jOOQ codegen) move behind the Postgres
binding. This matches how the methodology already frames storage ("a profile
detail") and avoids duplicating the transport.

**Recommended: Option B.** It keeps one copy of the transport and makes the
storage choice a config line, which is exactly the story the docs now tell.

### Sub-decisions

1. **Naming.** Create `java-micronaut` (Option B) and **retire the fused
   `java-micronaut-postgres` module** (its content becomes the Postgres binding
   inside `java-micronaut`), or keep `java-micronaut-postgres` as the
   Postgres-configured *deployment* and add `java-micronaut` as the in-memory
   service? Proposed: **one module `java-micronaut`**, Postgres selected by
   config; the Docker/Fly.io assets stay (they deploy the Postgres config).
2. **Config key.** A new `clad.storage` (`memory` | `postgres`) resolved in the
   `@Factory`; the existing `clad.properties storage.layer` prose stays
   descriptive. Ties to storage-layer selection generally.
3. **Default.** In-memory default (so the module runs with no Docker), Postgres
   for the durable deployment — mirroring `test.command`'s "without Docker"
   scoping.
4. **What is untouched.** `legible-engine`, `legible-storage`,
   `java-legible`, `java-plain`, and the fire-after-commit contract.

## Mechanism

The storage choice is a Micronaut bean selection: `MemoryStorageFactory`
(reference-impl/java-micronaut/src/main/java/com/example/app/storage/MemoryStorageFactory.java:20)
is active unless the postgres property is set and binds `InMemoryFactStore`;
`PostgresStorageFactory`
(reference-impl/java-micronaut/src/main/java/com/example/app/storage/postgres/PostgresStorageFactory.java:26)
is `@Requires(property = "clad.storage", value = "postgres")` and binds
`RmapPostgresFactStore`. `CladEngineFactory.syncEngine(FactStore)`
(reference-impl/java-micronaut/src/main/java/com/example/app/engine/CladEngineFactory.java:30)
depends only on the SPI, so the same concepts and syncs run on either binding.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Same app, same syncs/outcomes; storage binding is the only change |
| Action ordering and sync deduplication | `preserved` | Engine unchanged |
| Flow-token lineage | `preserved` | Engine unchanged |
| Storage/retention semantics | `preserved` | Postgres binding unchanged; in-memory binding added |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `reference-impl/README.md`, the profile READMEs, `methodology/implementation/STORAGE_MAPPING.md` |
| Profile configuration or deployment files | yes | reactor `pom.xml`; module poms; `Dockerfile`/`docker-compose.yml`/`fly.toml` paths; `application.yml` |
| Engine/runtime implementation | no | — |
| Profile tests | yes | the app's tests run against the selected binding (in-memory by default; Postgres under Testcontainers) |
| UC artefact chain | no | — |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Micronaut app boots on in-memory (no Docker) | integration | `mvn test -f reference-impl/pom.xml -pl java-micronaut -am` | pass | 16 tests, BUILD SUCCESS, no Docker |
| Micronaut app boots on Postgres (Testcontainers) | integration | `mvn test -f reference-impl/pom.xml -pl java-micronaut -am -Dclad.storage=postgres` | pass | 16 tests, BUILD SUCCESS |
| Concept + flow + ArchUnit suites pass on both bindings | integration | module test suite | pass | concept (in-memory) + flow + ArchUnit 5, both bindings |
| Full reactor unaffected | integration | `mvn test -f reference-impl/pom.xml` | pass | BUILD SUCCESS (engine, plain, legible, bench, storage, micronaut) |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 254 passed |

## Gates

### Design gate

To be approved before implementation. The gate's subject is **Option A vs. B**
and sub-decisions 1–3. Approve with
`./clad approve-maintenance micronaut-transport-storage-split design`.

### Evidence gate

Cleared: the module builds and its 16 tests pass on **both** bindings (in-memory default, no Docker; Postgres via `-Dclad.storage=postgres` with Testcontainers); the full reactor is BUILD SUCCESS; the durable deploy assets (Docker/Fly/compose) select the Postgres binding via `CLAD_STORAGE=postgres`; docs and `clad.properties` reflect the one-module, config-selected shape. Artefact pipeline intact (0 WARNs); gate suite green at 254.

## Notes

- **Blast radius is real:** a new module + a moved package tree + CI/test-command
  and Docker/Fly paths. It lands as its own design-gated change, not folded into
  docs work.
- **Relationship to the roadmap:** this is the "java-micronaut transport/storage
  split" backlog item; the Jena demotion (`jena-backend-demotion`) already
  removed the other unshipped backend.
- **Scope guard:** no change to the methodology, stage contracts, or the
  canonical profile; this is the reference stack only.
