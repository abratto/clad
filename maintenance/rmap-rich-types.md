# Maintenance change — `rmap-rich-types`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `quality-gate/rmap.py`,
  `reference-impl/legible-storage`, `reference-impl/java-micronaut`,
  `reference-impl/java-plain`; `clad.properties`; architecture/lowering docs.
- **Feature-contract impact:** `preserved` (no login action outcome, response
  contract, or flow-token change; the shipped login schema stays byte-identical)
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Add a small built-in scalar type map and a pluggable
  value-codec registry so CLAD can lower `Decimal`, `UUID`, `Date`, `Time`,
  `JSONB`, and `Bytes` columns and let downstream applications map their own
  domain types without guessing a fixed type set up front.
- **Dependent re-entry:** none

## Mechanism

- **Python type map.** `quality-gate/rmap.py` maps the built-in scalar names
  (`Int`, `Timestamp`, `Boolean`, `Decimal`/`Numeric`, `UUID`, `Date`, `Time`,
  `Json`/`JSON`/`JSONB`, `Bytes`) to SQL types; `Decimal(12,2)` renders
  `NUMERIC(12,2)`. A project/feature type map
  (`storage.type.<Name>=<SQL>` in `clad.properties`, or a feature-local
  `_config/type-map.md`) adds domain types. Unregistered domain value types keep
  the historical `TEXT` fallback; `storage.type.strict=true` rejects them.
- **Java codec registry.** `dev.legible.storage.ValueCodec` converts between
  the engine's string facts and a column's SQL value. `ValueCodecs` provides
  built-ins for TEXT/INTEGER/TIMESTAMP/BOOLEAN/NUMERIC/UUID/DATE/TIME/JSONB/
  BYTEA and loads custom codecs through `ServiceLoader`; an unknown SQL type
  fails loudly. `RmapPostgresFactStore` binds/reads every column through the
  codec instead of a hard-coded switch.
- **Identity columns stay TEXT.** The engine's `Region` SPI addresses subjects
  as strings; richer types apply to fact values in this change, not to
  individual identifiers.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Login models use only TEXT/INTEGER/TIMESTAMP; their derived schema/descriptor must stay byte-identical. |
| Action ordering and sync deduplication | `preserved` | No engine or sync change. |
| Flow-token lineage | `preserved` | Flow log untouched. |
| Storage/retention semantics | `changed` (extended) | Derived apps can use numeric/uuid/date/time/jsonb/bytea fact columns; the runtime round-trips them through the codec registry. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `RMAP_CONFORMANCE.md`, `DATA_MODEL_NOTES.md`, `RELATIONAL_LOWERING.md`, `clad.properties`. |
| Profile configuration or deployment files | yes | `storage.type.*` / `storage.type.strict` documented; no required key for existing apps. |
| Engine/runtime implementation | yes | `legible-storage` gains `ValueCodec`/`ValueCodecs`; `RmapPostgresFactStore` uses them. |
| Profile tests | yes | New `RichTypes` fixture and `RmapEdgeBehaviorTest` P11; Python type-map tests. |
| UC artefact chain | no | Frozen login models and examples are unchanged. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Built-in scalar types render the expected SQL types | unit | `test_rmap_conformance.py` | pass | `RichTypeConformanceTests` |
| Domain type map and strict mode behave as specified | unit | `test_rmap_conformance.py` | pass | `test_type_map_overrides…`, `test_strict_types…`, `test_type_config…` |
| Runtime codecs round-trip NUMERIC/UUID/DATE/TIME/JSONB/BYTEA | integration (Testcontainers) | `RmapEdgeBehaviorTest` P11 | pass | `richScalarTypesRoundTrip` |
| Login migration and descriptor stay byte-identical | drift guard | `./clad rmap --check`, `verify_rmap_descriptor.py` | pass | both profile migrations and the descriptor report current |
| Full Python and PostgreSQL gates stay green | gate | `pytest`, `verify_artefacts.py`, postgres reactor | pass | pytest 660 passed; artefact pipeline intact; reactor 49/47/39/20/1 BUILD SUCCESS |

## Gates

### Design gate

Approved in-conversation (2026-11-17): a small built-in scalar set plus a
declarative type map and a `ValueCodec` SPI; unknown SQL types fail loudly,
while unregistered domain value types remain `TEXT` unless strict mode is on.

### Evidence gate

Approved (2026-11-17). Evidence: `pytest quality-gate/tests -q` → 660 passed;
`verify_artefacts.py` → artefact pipeline intact; `mvn -B -ntp verify -f
reference-impl/pom.xml -pl legible-storage,java-micronaut,java-plain -am
-Dclad.storage=postgres` → 49/47/39/20/1 BUILD SUCCESS; both login migrations
and the login descriptor report current; `RmapEdgeBehaviorTest` P11 round-trips
NUMERIC/UUID/DATE/TIME/JSONB/BYTEA through the codecs.

## Notes

- Non-goals this change: UUID/typed primary keys (the SPI remains string-based);
  per-column decimal precision enforcement beyond the SQL type; JSON schema
  validation; a GUI/config writer for the type map.
- Rollback: revert the branch; the previous `TEXT`/integer/timestamp/boolean
  mapping is the default.
