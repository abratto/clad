# Maintenance change — `engine-extraction`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/java-micronaut-jena` (establishes the shared `clad-engine` module consumed by future profiles, incl. `java-micronaut-postgres`)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Extract the profile-agnostic action-log coordination engine from `java-micronaut-jena` into a shared `clad-engine` Maven module under the stable `dev.clad.engine` package.

## Why

The coordination engine (action-log polling, sync dispatch, flow archival) is
identical regardless of how concept *state* is persisted. Today it lives inside
`java-micronaut-jena` at `com.example.app.engine`, so a second profile
(`java-micronaut-postgres`) would have to copy it — and copies drift.

This change moves the engine into a single shared module both profiles depend
on, so a future engine fix lands once, everywhere. The engine only ever touches
the **in-memory Jena action log** (`LocalStorage`); the durable-backend pieces
(`SplitStorage`, `RemoteStorage`, `CladDatasetFactory`) stay in the Jena profile
where they belong.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | No SPARQL, outcome, or `Web/respond` change; pure move |
| Action ordering and sync deduplication | preserved | `ConceptAgent`/`SyncAgent`/`SyncDispatcher` logic moved verbatim; dedup guards unchanged |
| Flow-token lineage | preserved | `FlowManager`/`FlowArchiver` moved verbatim |
| Storage/retention semantics | preserved | The shared module carries only `LocalStorage` (in-memory action log); `SplitStorage`/`RemoteStorage`/`CladDatasetFactory` remain in the Jena profile unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | README package map, `CODE_STYLE.md` package table + R4 engine-type lists, `ENGINE.md` component file paths |
| Profile configuration or deployment files | yes | `clad.properties` (`test.command` → reactor root; impl paths unchanged — concepts/syncs do not move) |
| Engine/runtime implementation | yes | Move 20 engine classes `com.example.app.engine` → `dev.clad.engine` in a new `reference-impl/clad-engine` module; introduce a parent `reference-impl/pom.xml` reactor |
| Profile tests | yes | `LegibleArchitectureRulesTest` (`SOURCE_ROOT`, `ENGINE_RUNTIME_TYPES`, `PRIMARY_ADAPTER_ENGINE_TYPES` FQNs), concept/sync tests update engine imports |
| UC artefact chain | no | No concept/sync/spec slice changes; stage sequence unchanged |

## Design (file-by-file)

### Reactor structure

```
reference-impl/
├── pom.xml                 (parent: packaging=pom, depMgmt, shared versions)
├── clad-engine/            (NEW — shared coordination engine)
│   └── src/main/java/dev/clad/engine/
│       ActionLog, ActionRecord, CompletionBus, ConceptAgent, DevNullSink,
│       FlowArchiver, FlowArchiveBuffer, FlowArchiveException, FlowArchiveSink,
│       FlowManager, LocalStorage, LoggerSink, RdfVocabulary,
│       Storage, SyncAgent, SyncDispatcher, SyncEvaluationException,
│       SyncEvaluator, SyncMetadata, SyncTrigger
└── java-micronaut-jena/    (module; keeps storage/ (SplitStorage, RemoteStorage,
                             CladDatasetFactory), tdb2/fuseki, concepts, syncs,
                             api/ResponseAssembler)
```

GroupId stays `com.example.clad` (matches the existing profile). The engine
*Java package* becomes `dev.clad.engine`; the *app* package (`com.example.app`
for concepts/syncs/api/infrastructure) is unchanged.

### Moves (20 classes, verbatim except `package` + imports)

All classes listed above move from
`reference-impl/java-micronaut-jena/src/main/java/com/example/app/engine/` to
`reference-impl/clad-engine/src/main/java/dev/clad/engine/`. Only the `package`
declaration changes (they are self-contained — no `com.example.app` imports).
`LocalStorage` visibility changes `class` → `public class` (the Jena profile's
`CladDatasetFactory` constructs it from outside the package). `RdfVocabulary.conceptGraph(...)`
stays in the shared vocab (harmless helper; unused by non-RDF profiles).

### Stays in the Jena profile

- `SplitStorage`, `RemoteStorage`, `CladDatasetFactory` — move to
  `com.example.app.storage` and add `import dev.clad.engine.*` (they implement
  the shared `Storage` SPI for durable routing).
- `ResponseAssembler` — moves to `com.example.app.api` (it maps flow fields to
  profile-specific `api` DTOs, so it is not profile-agnostic and cannot join
  the shared module).
- Concepts (`concepts.user/passwordauth/session`), syncs (`syncs`), `api`,
  `infrastructure` — unchanged except engine imports.

### Concept/sync import updates

Every `import com.example.app.engine.*` in `java-micronaut-jena` (concepts,
syncs, infrastructure, `Application`, tests) becomes `import dev.clad.engine.*`.
No other edits.

### Config + docs

- `clad.properties`: `test.command` → `mvn test -f reference-impl/pom.xml`
  (reactor root). `sync.impl.dir`, `concept.impl.dir`, `test.source.root` stay
  as-is (concepts/syncs do not move).
- `LegibleArchitectureRulesTest`: `SOURCE_ROOT` unchanged; `ENGINE_RUNTIME_TYPES`
  and `PRIMARY_ADAPTER_ENGINE_TYPES` FQNs → `dev.clad.engine.*`; import both
  `com.example.app` and `dev.clad.engine`.
- Review `quality-gate/verify_action_log_isolation.py` and the parity scripts
  for any `com.example.app.engine` string they key off; update to `dev.clad.engine`
  where they scan the engine package.

### Non-goals

- No behavior change to any class (move-only, modulo package/imports).
- No change to concepts, syncs, specs, SPARQL, the stage sequence, or
  `quality-gate/advance.py` protocol.
- No `java-micronaut-postgres` profile in this record (separate
  `maintenance/postgres-reference-profile.md`).

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Engine coordination unchanged | unit | `ConceptAgentTest` (11), `ConceptAgentLoadTest` (2) in `clad-engine`; `SyncTestBase`, `ConceptTestBase` | pass | 13/13 green |
| Full login flow resolves (200/401) | flow-regression | `CucumberTest` (4), `EngineTimingTest` (2), `DebugControllerTest` (6) | pass | 0 failures |
| ArchUnit rules pass against new package | unit | `LegibleArchitectureRulesTest` (18), `CladRulesComplianceTest` (2) | pass | 0 violations |
| No residual `com.example.app.engine` in profile | unit | `grep -r "com.example.app.engine" reference-impl/java-micronaut-jena/src reference-impl/clad-engine/src` → 0 | pass | 0 matches |
| Concurrency unaffected | integration | `ConcurrencyTest` (1–32 threads) | pass | 0 errors, ~114–228 req/s |
| Full regression | integration | `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml` | pass | gate PASS, 80 tests 0 failures |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before any
implementation. Approve with `./clad approve-maintenance engine-extraction design`,
then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- **Cross-repo compatibility (clad-agent):** the namespace rename is engine-only —
  the `com.example.app` app package, `_config/package-and-layout.md` semantics,
  `quality-gate/advance.py`, and the stage sequence are all untouched, so
  clad-agent's `STAGE_ORDER` mirror, test fixtures, and knowledge bundle are
  unaffected.
- **Adoption-model change:** downstream projects will depend on `clad-engine`
  (reactor module) rather than copying a single self-contained profile folder.
  Update `reference-impl/README.md` copy-out guidance accordingly.
- **Coupling-gate refinement:** the package move rewrites only `import`/`package`
  lines in the concept/sync classes, which `verify_iterative_change_coupling.py`
  previously flagged as spec-decoupled changes. The gate now treats import/package-only
  diffs as Presentation changes (R17) and skips them; regression coverage added in
  `quality-gate/tests/test_iterative_change_coupling.py`.
