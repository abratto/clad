# Maintenance change — `jena-backend-demotion`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-storage` (build/test surface); docs across `reference-impl/` and `methodology/`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** CLAD ships no Jena/TDB persistence profile. Remove `JenaFactStore` from the supported build (delete the implementation + its test + the Jena dependency), and sweep the remaining "in-memory/Jena/Postgres" phrasing in the architecture/implementation docs and root `clad.properties` so only the shipped backends (in-memory, Postgres) read as supported. Anyone who wants RDF/SPARQL persistence implements the `FactStore` SPI.

## Why

The legacy RDF/SPARQL (Jena) **profile** was retired (`reference-impl/LEGACY.md`);
what remained was a working `JenaFactStore` inside `legible-storage` that kept
Jena in the reactor and in every "storage is swappable" sentence. That creates
mixed signals — a backend that is tested and shipped but whose profile is
retired — and it commits CLAD to maintaining an RDF dependency for a narrow
audience. The paper's own implementation moved off RDF/SPARQL, and the
canonical/durable profiles use in-memory and Postgres.

The clean position: **the `FactStore` SPI is the extension point; CLAD ships
in-memory and Postgres; RDF/SPARQL is a backend you implement.** This record
makes the code and the docs match that position.

## Rule

- **Code.** Delete `JenaFactStore.java` and `JenaFactStoreTest.java`; remove the
  `jena-arq` dependency from `legible-storage/pom.xml` and the `jena.version`
  property from the reactor `pom.xml`. `StorageContractTest` and the Postgres
  backends are unaffected.
- **Docs.** Reword the remaining Jena-as-a-shipped-backend phrasing to
  "in-memory (canonical) and Postgres (durable); another backend — e.g. RDF —
  is a `FactStore` you provide":
  - `reference-impl/legible-storage/README.md` (drop the `JenaFactStore` bullet;
    fix the StorageContractTest sentence),
  - `methodology/architecture/ENGINE.md` (`InMemoryFactStore` canonical;
    Postgres implements the SPI),
  - `methodology/architecture/SYNC_PATTERNS.md`,
  - `methodology/implementation/STORAGE_MAPPING.md` (the named-graph example
    becomes "if your own backend stores named graphs"),
  - root `clad.properties` (`storage.layer` examples).
- **Historical references stay.** `SYNC_ENGINE_EVOLUTION.md`, `LEGACY.md`,
  `ORIGINS.md`, `CITATIONS.md`, `DECISIONS.md`, and R21 describe the *retired*
  engine and are accurate history — they are not changed.
- **Features.** `templates/storage-rdf-example.md` already says CLAD ships no RDF
  profile; keep it as an illustrative shape.

## Mechanism

The change removes `JenaFactStore` and its test from `legible-storage` and
drops the `jena-arq` dependency (reference-impl/legible-storage/pom.xml:21),
leaving the Postgres backends — `RmapPostgresFactStore` (relation realization)
and `PostgresFactStore` (generic fact relation) — as the module's implementations
of the engine SPI `FactStore` (reference-impl/legible-engine/src/main/java/dev/legible/engine/FactStore.java:8).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Removing an unused backend; no engine/spec change |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | In-memory + Postgres unchanged; Jena removed from build |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `ENGINE.md`, `SYNC_PATTERNS.md`, `STORAGE_MAPPING.md`, `legible-storage/README.md`, `clad.properties` |
| Profile configuration or deployment files | yes | reactor + `legible-storage` poms (drop Jena) |
| Engine/runtime implementation | no | — |
| Profile tests | yes | delete `JenaFactStoreTest` |
| UC artefact chain | no | — |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| `legible-storage` builds without Jena | integration | `mvn test -f reference-impl/pom.xml -pl legible-storage` | pass | BUILD SUCCESS (18 tests) |
| Postgres + contract suites still pass | integration | `legible-storage` suite | pass | RmapPostgres 5, RmapDeriver 4, PostgresFactStore 9 |
| No Jena reference remains in the build | unit | `grep -rin jena reference-impl/*/pom.xml` | pass | no matches; no `*Jena*.java` files remain |
| Canonical profile unaffected | integration | `mvn test -f reference-impl/pom.xml -pl java-legible -am` | pass | BUILD SUCCESS (40 tests) |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 254 passed |

## Gates

### Design gate

To be approved before implementation. The decision at stake is **delete** vs.
**keep-but-exclude-from-CI**: this record proposes **delete** (the store is 113
lines, reproducible from the SPI, and keeping an unbuilt backend is exactly the
mixed signal being removed). Approve with
`./clad approve-maintenance jena-backend-demotion design`.

### Evidence gate

Cleared: `legible-storage` (18 tests) and the canonical profile (40 tests) build green without Jena; no `jena` reference remains in any pom or Java file; the docs and root `clad.properties` are swept. Artefact pipeline intact (0 WARNs); gate suite green at 254.

## Notes

- **Reversibility.** The store is small and the SPI is stable; a future project
  needing RDF can re-derive it from `LEGACY.md` (`v0.4.0`) or implement the SPI.
- **Relationship to the roadmap.** This is the "Jena backend demotion" backlog
  item; the `java-micronaut` transport/storage split is the separate follow-up.
