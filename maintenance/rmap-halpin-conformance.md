# Maintenance change — `rmap-halpin-conformance`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-storage`,
  `reference-impl/java-micronaut`, `reference-impl/java-plain`;
  `quality-gate/rmap.py`, `quality-gate/verify_data_model.py`,
  `methodology/architecture/`
- **Feature-contract impact:** `preserved` (no login action outcome, response
  contract, or flow-token change; the shipped login schema stays byte-identical)
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Align CLAD's relational procedure with the supported
  subset of Halpin's Rmap: preserve subtype constraints under absorption,
  realise ordinary intra-concept entity references as foreign keys when the
  target owns stored state, and publish the supported-subset contract with
  Halpin-derived valid/invalid population tests.
- **Dependent re-entry:** none

## Mechanism

- **Absorption preserves conditional mandatory roles.** Facts owned by an
  absorbed subtype are nullable columns on the supertype's table, with a
  membership `CHECK` that allows all-null (non-member) or all effective
  mandatory facts present (member). `quality-gate/rmap.py` will carry each
  fact's `source_type` through grouping so the supertype table can distinguish
  its own facts from a subtype's.
- **Entity references become FKs only when the target can hold a row.** The
  deriver resolves a fact value type against the concept-local object-type and
  reference-scheme declarations. A target whose table has at least one data
  column gets `FOREIGN KEY`; an identity-only target stays an opaque value and
  emits a warning. This matches the existing child-table rule
  (`reference-impl/java-micronaut/RELATIONAL_LOWERING.md` §Guardrails) and the
  runtime SPI, which has no identity-materialisation operation
  (`reference-impl/legible-engine/src/main/java/dev/legible/engine/Region.java`).
- **Unsupported targets fail loudly.** A reference to a partitioned supertype
  is a derivation error; a compidot reference is outside the supported grammar
  (a fact value cannot name a composite subject); an FK cycle is a derivation
  error. Tables are topologically ordered so inline FKs reference an
  already-created table, which keeps `RmapPostgresFactStore.createSchema()`
  correct because it executes each table's embedded `ddlText`.
- **The supported subset is documented.** `methodology/architecture/RMAP_CONFORMANCE.md`
  records Halpin's stages, what CLAD derives versus supplies, the supported
  grammar subset, and the explicit non-goals (role-level 1:1 orientation,
  general set-comparison constraints, derived-fact views, composite-reference
  FKs). The overclaim "Halpin's Rmap, complete" is removed.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Login data models contain no same-concept entity references and no absorbed subtypes; their derived schema/descriptor must stay byte-identical. |
| Action ordering and sync deduplication | `preserved` | No engine or sync change. |
| Flow-token lineage | `preserved` | Flow log untouched. |
| Storage/retention semantics | `changed` | Derived apps gain FKs and conditional subtype checks; absorbed-subtype facts become nullable and retracting one ceases subtype membership without deleting the supertype row. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `RELATIONAL_RMAP.md`, `RELATIONAL_LOWERING.md`, `STORAGE_MAPPING.md`, `DATA_MODEL_NOTES.md`, new `RMAP_CONFORMANCE.md`, `CITATIONS.md`. |
| Profile configuration or deployment files | no | No config keys changed. |
| Engine/runtime implementation | no | No engine change; `quality-gate/rmap.py` and `verify_data_model.py` only. The runtime consumes the new descriptor/DDL. |
| Profile tests | yes | Domain schema fixtures and migration oracles regenerate; new PostgreSQL probes for absorption and entity FKs. |
| UC artefact chain | no | Frozen login data models are unchanged; no feature re-entry. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Absorbed subtype mandatory facts are nullable and guarded by a membership check | unit | `quality-gate/tests/test_rmap.py`, `test_rmap_conformance.py` | pass | `test_absorb_moves_subtype_facts_to_parent`, `AbsorptionConformanceTests` |
| Absorbed subtypes without a mandatory qualifier, with defaults, or with multi-valued facts are rejected | unit | `quality-gate/tests/test_machine_model_parser.py`, `test_rmap_conformance.py` | pass | `DataModelSemanticsConformanceTests` + derivation negative tests |
| Same-concept entity references to state-owning targets render FKs; identity-only targets stay opaque with a warning | unit | `test_rmap_conformance.py` | pass | `EntityReferenceConformanceTests` |
| Partitioned/compidot targets and FK cycles fail loudly | unit | `test_rmap_conformance.py` | pass | partitioned target, FK cycle, cross-concept FK tests |
| Inline FKs are topologically ordered and `--alter` adds new FK constraints | unit | `test_rmap.py`, `test_rmap_conformance.py` | pass | topological-order and `test_alter_adds_a_new_entity_foreign_key` |
| Absorbed subtype population and entity-reference FK enforcement | integration (Testcontainers) | `RmapEdgeBehaviorTest` | pass | P6 conditional mandatory, P7 missing-target FK, P8 action-boundary promotion/retract; legible-storage 36/36 |
| Unsupported derived facts are rejected, not stored | unit | `test_rmap_conformance.py`, `verify_data_model` tests | pass | derivation raises; Stage 03b reports the fact |
| Login migration and descriptor stay byte-identical | drift guard | `./clad rmap --check`, `verify_rmap_descriptor.py` | pass | both profile migrations and the descriptor report current |
| Full Python and PostgreSQL gates stay green | gate | `pytest`, `verify_artefacts.py`, postgres reactor | pass | pytest 634 passed; artefact pipeline intact; reactor 49/47/36/20/1 BUILD SUCCESS |

## Gates

### Design gate

Approved in-conversation (2026-11-14): Phase A + B + C; defer Phase D.
Identity-only reference targets follow the "FK only when the target has data
columns" rule; `absorb` requires at least one mandatory simple qualifier.

### Evidence gate

Approved (2026-11-17). Evidence: `pytest quality-gate/tests -q` → 634 passed;
`verify_artefacts.py` → artefact pipeline intact; `mvn -B -ntp verify -f
reference-impl/pom.xml -pl legible-storage,java-micronaut,java-plain -am
-Dclad.storage=postgres` → 49/47/36/20/1 BUILD SUCCESS; both login migrations
and the login descriptor report current; Testcontainers probes P6 (conditional
mandatory absorption), P7 (entity-reference FK), and P8 (action-boundary
promotion/retract) are green. A throwaway experiment harness also covered
Halpin 1:1 orientation, 3-role objectification, generated Stage 03b models,
random populations, and `--alter` migration edges (0 failures).

## Notes

- Compatibility: the login schema is unchanged. Derived apps with same-concept
  entity references gain FKs; apps with absorbed subtypes gain nullable columns
  and `CHECK` constraints. A migrated app must use `--alter` and review the new
  constraints.
- Non-goals this change: role-level annotation and derived 1:1 orientation;
  general subset/equality/exclusion constraints; derived-fact SQL views;
  composite-reference and compidot-reference FKs. Deferred to a later change.
- Rollback: revert the branch; the previous schema is reproduced by the prior
  `rmap.py` and fixture set.
