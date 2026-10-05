# Maintenance change — `rmap-table-set-storage`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval) — the port is complete and
  evidence-approved on this branch; close the record when it merges to `main`.
- **Affected profile(s):** `reference-impl/legible-engine`,
  `reference-impl/legible-storage`, `reference-impl/java-legible`,
  `reference-impl/java-micronaut` (the durable shared surface)
- **Feature-contract impact:** `preserved` (no example-UC action outcome,
  response contract, or flow-token change)
- **Design gate:** `approved` (approved in the source experiment — see
  provenance below; this record reflects the same approved design)
- **Evidence gate:** `approved`
- **Change summary:** Port the experiment-validated **Rmap rewrite** upstream:
  a concept region is a **table set** (`RmapModel`) rather than always one
  table; the `Region` SPI gains composite-subject overloads and the engine a
  capability-located `TransactionalRegion`; the relational deriver implements
  Halpin's Rmap completely (multi-object-type regions, compound subjects,
  multi-valued child tables, subtyping with per-model absorb/separate/partition,
  independent object types); the Postgres store buffers writes per action
  (mandatory → `NOT NULL`), buffers retracts (remove-then-write coalesces), and
  writes TIMESTAMP as ISO-8601 instants.

## Provenance

This change was designed, implemented, reviewed, and proven in the
`legalcare-clad` experiment first (the deliberate route: experiment, then
port upstream). Commits `cc80c89`, `d82c9cb`, `5dd59e8`, `2f7e74b` there
carry the maintenance records (`maintenance/rmap-rewrite-handover.md`,
`maintenance/rmap-subtyping.md` — design and evidence gates approved and
closed) whose decisions this port transcribes:
- The human's composite-subject decision ("option 3 done right"): the
  individual **is** the component pair; no surrogate id, no mapping
  table (`Region`'s list-subject overloads).
- Subtype mapping is an explicit per-model annotation
  (`mapping: absorb | separate | partition`; separate default) — no
  population inference; existing schemas re-derive byte-identically.
- Derived facts → SQL views are **tabled with a note** in the lowering docs
  (no SQL consumer in the concept layer; BI would re-enable as a gated
  decision).

## Mechanism

- `Region` gains the list-subject overloads (`read/write/remove/clear(List)`,
  defaulting to the joined form) — the engine SPI for composite reference
  schemes (`reference-impl/legible-engine/src/main/java/dev/legible/engine/Region.java`).
- `FactStore.maybeRegion` (default → `region`) lets the engine tolerate
  stateless concepts.
- `TransactionalRegion` (opt-in capability): `SyncEngine.execute` wraps
  concept actions `beginAction/flushAction/abortAction`
  (`.../engine/SyncEngine.java`), so a relational region flushes one
  statement per row and mandatory columns arrive together (`NOT NULL`).
- `RmapModel` (new) carries the table set; `RmapDeriver#deriveModel` parses
  unary/binary/n-ary `## State` notation (compound `(A,B)->V`, multi-valued
  `{V}`/prose, subtype declarations, `independent T`) and realises stages
  1–4; unparseable relation lines throw instead of dropping silently.
- `RelationSchema` grows composite PK, `NOT NULL`, `UNIQUE`, `CHECK`,
  intra-concept FKs, identity/data column split (`identityColumns()`),
  and the derived flag; `RmapMigration` renders full model sets.
- `RmapPostgresFactStore` routes facts across the table set: identity columns
  come from the object type (not name heuristics), buffered retracts
  coalesce at flush, a mandatory-no-default retract deletes the row, and
  multi-valued facts flush as child-table rows. A single-fact write outside an
  engine action updates an existing row in place (never `INSERT … ON CONFLICT
  DO UPDATE`, whose proposed insert tuple PostgreSQL validates for `NOT NULL`
  *before* resolving the conflict — so a partial upsert of a mandatory
  multi-column row is rejected for its absent sibling); when the fact's column
  is part of a composite key (a multi-valued child table) each distinct value
  inserts as its own row and siblings are never overwritten. A lone write to an
  unknown individual with a mandatory no-default sibling fails `NOT NULL`
  loudly rather than inventing a value.
- `InMemoryFactStore.read(String,…)` answers partial composite keys by a
  prefix scan over joined subjects (a sync's Pattern-D read by the leading
  key component). TIMESTAMP SPI values are ISO-8601 instant strings on both
  backends; **both** `PasswordAuthConcept`s (the `java-legible` example and the
  `java-micronaut` app concept) are normalized to that wire encoding — the app
  concept writes `Instant.ofEpochMilli(...).toString()` and reads
  `Instant.parse(...).toEpochMilli()`, matching the store's `fromSpi`/`toSpi`
  (`RmapPostgresFactStore`). A prior port revision left the app concept on
  epoch-millis while the store read ISO, which fails under
  `clad.storage=postgres` with a `NumberFormatException` on the second lock
  check; `PasswordAuthTimestampTest` (Testcontainers) now guards it.
  `java-micronaut`'s `V1` migration is regenerated by its own drift guard
  (NOT NULL/typing), proving no silent drift at the profile.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | The example UC-00 flow suite and every profile test are green (`mvn -f reference-impl/pom.xml test`: 41/47/35/21; the 4 Docker ITs run under `-Dclad.storage=postgres`). |
| Action ordering and sync deduplication | `preserved` | Engine change is the transactional wrapper around `execute` only. |
| Flow-token lineage | `preserved` | Flow log untouched. |
| Storage/retention semantics | `preserved` (extended) | In-memory store keeps single-region semantics; gains prefix reads; no existing `Region` caller changes. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `RELATIONAL_LOWERING.md` (subtypes, tabled views) + `methodology/implementation/STORAGE_MAPPING.md` (table-set Rmap). |
| Profile configuration or deployment files | no | No config keys changed. |
| Engine/runtime implementation | yes | `legible-engine`: `Region`, `FactStore`, `InMemoryFactStore`, `SyncEngine`, new `TransactionalRegion`; `legible-storage`: `RmapModel` (new), `RelationSchema`, `RmapDeriver`, `RmapMigration`, `RmapPostgresFactStore`. |
| Profile tests | yes | New: `RmapDeriverModelTest`, `RmapCompositeSubjectTest` (Testcontainers), `PasswordAuthTimestampTest`, and two write-path regressions in `RmapPostgresFactStoreTest`. `RmapPostgresPersistenceIT` renamed to `RmapPostgresPersistenceTest` so surefire discovers it (an `*IT` name is not run by the reactor's surefire, so the persistence evidence had never executed). |
| UC artefact chain | no | No concept/sync spec changes; examples' state unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Deriver: table sets, compound/multi-valued, subtyping, independent types, byte-identical existing output | unit | `RmapDeriverTest` (4), `RmapDeriverModelTest` (14) | pass | `mvn -f reference-impl/pom.xml test` — legible-storage module; `existingSchemasReDeriveByteIdentical` holds (frozen UC-00 DDL). |
| Region SPI composite-subject round-trips on Postgres | integration (Testcontainers) | `RmapCompositeSubjectTest` (1) | pass | Composite-PK table + multi-valued child table on `postgres:16-alpine`. |
| Store serves transactions across table sets (NOT NULL, retracts, ISO instants) | integration (Testcontainers) | `RmapPostgresFactStoreTest` (7), `PostgresFactStoreTest` (9) | pass | Lockout flow (INTEGER + TIMESTAMP coercion), composite routing, partial-key prefix read, single-fact update-in-place of a mandatory row, and a lone write to an unknown individual rejected (not fabricated). |
| Persistence profile: Flyway owns the base schema, R-map shape has no cross-concept FK, jOOQ ↔ engine store agree | integration (Testcontainers, `@MicronautTest`) | `RmapPostgresPersistenceTest` (3) | pass | Renamed from `*IT` so it actually runs under `-Dclad.storage=postgres`; its jOOQ-visible engine-write case exposed the partial-upsert NOT NULL bug above. |
| App concept's `lockedUntil` is ISO-8601 on the wire through the real SyncEngine (not epoch-millis) | integration (Testcontainers) | `PasswordAuthTimestampTest` (1) | pass | `-Dclad.storage=postgres`; lock persists ISO, lockout rejects a correct password. Fails on the pre-fix epoch-millis read with `NumberFormatException`. |
| Example profile stays contract-green (login flows, migration drift) | profile | `mvn -f reference-impl/pom.xml test` (reactor) | pass | Default reactor: 41 (engine) / 47 (bench) / 35 (storage) / 21 (java-micronaut, of which 4 Docker ITs skip without `-Dclad.storage=postgres`) incl. LoginFlowTest + the drift-guard-regenerated V1. Under `-Dclad.storage=postgres` the 4 run and pass. |
| Canonical `test.command` gate green | gate | `test.command` (`verify_artefacts.py && mvn -pl java-legible -am`) | pass | exit 0 on the port branch; artefact gate + java-legible chain (41/47) green. |
| Artefact pipeline intact after doc changes | gate | `python3 quality-gate/verify_artefacts.py` | pass | RESULT: artefact pipeline intact; docs' cross-references resolve. |

## Gates

### Design gate

Approved in the source experiment (see Provenance and
`legalcare-clad/maintenance/rmap-subtyping.md` — design gate approved there
before implementation).

### Evidence gate

Approved — the test matrix above is the evidence: reactor green
(41 engine / 47 bench / 35 storage incl. Testcontainers / 21 java-micronaut
of which 4 Docker ITs run under `-Dclad.storage=postgres`),
the canonical `test.command` gate exit 0, and the artefact pipeline intact.
The design was approved in the source experiment (see Provenance).

## Notes

- Compatibility: the `Region` interface is extended by **default methods**
  only (old `String` forms keep their semantics); `FactStore.maybeRegion`
  defaults to `region`. The in-memory store behavior for plain subjects is
  unchanged; a subject containing `\u0000` — the join separator reserved by
  `Region.map` — now also matches as a composite prefix, which no existing
  concept produces.
- Rollback: revert the branch; the previous single-table store remains
  tagged upstream.
- Migration text (`V1`) changes shape (NOT NULL etc.) *before* any release —
  consistent with the drift guard that demands the regeneration; deployed
  canonical users regenerate at adoption time under their own gates.
