# Maintenance change — `csdp-machine-model-to-rmap`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-storage`,
  `reference-impl/java-micronaut`, `reference-impl/java-legible` (the durable
  shared surface); plus the Stage 03b artifact contract
  (`templates/data-model.md`, `quality-gate/generate_data_model.py`,
  `quality-gate/verify_data_model.py`, `methodology/architecture/DATA_MODEL_NOTES.md`)
- **Feature-contract impact:** `preserved` (no use-case action outcome, response
  contract, flow-token, or derived-schema change — the machine block transcribes
  the same facts the `## State` notation already carries)
- **Design gate:** `approved` (human, in-conversation: adopt CLAD's
  CSDP-aligned machine-model block, not Jarrar's ORM-ML XML)
- **Evidence gate:** `approved`
- **Change summary:** Make the Stage 03b conceptual data model the canonical,
  machine-readable input to Halpin's Rmap: each `<Name>.data-model.md` gains a
  CSDP-aligned `## Machine model` block; `RmapDeriver` parses that block (via a
  new `deriveFromDataModel` entry) instead of the Stage 02 `## State` notation;
  the runtime `LoginSchemas` becomes a loader over the committed data-model
  files, and the Flyway drift guard regenerates from the same source.

## Mechanism

- **Artifact contract.** The block is a small, hand-authorable, CSDP-aligned
  notation (not XML). It names object types with their reference schemes, and
  one `fact` per elementary fact type carrying its arity, value type, and role
  annotations (`mandatory|optional`, `unique`, `default`, `in {…}`), plus
  `Sub is a Sup -- mapping: …` and `independent T`. It is emitted
  deterministically by `generate_data_model.py` from the concept `## State`
  relations and validated by `verify_data_model.py`.
- **Parsing.** `quality-gate/artifact_parsers.py` gains `parse_machine_model()`
  (the Python source of truth) feeding generation/validation;
  `RmapDeriver` gains a parser for the same block producing its existing
  internal `ParsedState`, so the Rmap *algorithm* is untouched — only the input
  adapter changes.
- **Runtime source.** `LoginSchemas` reads the committed
  `examples/UC-00-login/stages/03b_data-model/output/*.data-model.md` files and
  derives from them; `RmapDeriverTest` re-reads the same files so the schema
  cannot drift from the data model. `RmapMigrationTest` regenerates the Flyway
  migration from the data-model source (the migration bytes do not change).
- **Backward compatibility.** `RmapDeriver.derive(concept, stateNotation)` is
  retained as a deprecated shim over the same realization, so existing callers
  and tests that pass `## State` text keep working.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Same facts derive the same tables; the example flow suite and every profile test stay green. |
| Action ordering and sync deduplication | `preserved` | No engine change. |
| Flow-token lineage | `preserved` | Flow log untouched. |
| Storage/retention semantics | `preserved` | Derived schema is byte-identical; `V1__login_rmap.sql` regenerates unchanged. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `STORAGE_MAPPING.md`, `reference-impl/java-micronaut/RELATIONAL_LOWERING.md`, `methodology/architecture/DATA_MODEL_NOTES.md`, `templates/data-model.md`. |
| Profile configuration or deployment files | no | No config keys changed. |
| Engine/runtime implementation | yes | `legible-storage`: `RmapDeriver` (data-model parser + entry), `LoginSchemas` (loader); `legible-engine` unchanged. |
| Profile tests | yes | `RmapDeriverTest` (source switch), new equivalence/negative tests; `RmapMigrationTest` source switch. |
| UC artefact chain | no | `## State` unchanged; the machine block is a faithful transcription. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| `parse_machine_model` reads blocks; round-trips the generator's output | unit | `quality-gate/tests/test_machine_model_parser.py` (8) | pass | `python3 -m pytest quality-gate/tests` → 313 passed |
| `verify_data_model` requires/validates the block | gate | `quality-gate/verify_data_model.py` | pass | the three UC-00 data models PASS with the block present (storage leakage in the block is still caught by the existing whole-file leakage scan) |
| Data-model derivation equals the `## State` derivation (equivalence oracle) | unit | `RmapDeriverTest#dataModelAndStateInputsDeriveIdenticalSchemas` | pass | the three UC-00 concepts derive identical schemas from both inputs |
| Unparseable/absent machine block throws (no silent drop) | unit | `RmapDeriverDataModelTest` (6) | pass | missing section, unfenced block, and empty block all throw; compound/multi/subtype clauses realize |
| Example schema + Flyway migration unchanged by the source switch | integration (Testcontainers) | `RmapMigrationTest`, `RmapPostgresFactStoreTest` (7) | pass | `V1__login_rmap.sql` byte-identical (drift guard green, no regeneration); reactor under `-Dclad.storage=postgres`: 41/47/42/21 |
| Canonical `test.command` gate green | gate | `test.command` | pass | exit 0 (verify_artefacts + java-legible 41/47) |

## Gates

### Design gate

Approved in-conversation. Decision: adopt CLAD's CSDP-aligned block (not
Jarrar's ORM-ML XML — XML, diagram-shaped, external schema, and explicitly not
human-authored). Reuses the CSDP seven-step structure and Halpin/Jarrar's
constraint vocabulary; Rmap consumes the fact/constraint subset (fact types,
reference schemes, uniqueness, mandatory roles, value constraints, subtyping).

### Evidence gate

Approved — the matrix above is the evidence: pytest 313 passed
(8 new parser tests), the three UC-00 data models pass `verify_data_model.py`,
the equivalence oracle holds (`## State` ≡ machine block), negative cases throw,
`test.command` exit 0, and the reactor under `-Dclad.storage=postgres` is
green (41/47/42/21) with the Flyway migration byte-identical.

## Notes

- Compatibility: `RmapDeriver.derive(concept, stateNotation)` remains (deprecated
  shim); `deriveFromDataModel(concept, dataModelText)` is the new entry.
- The block is deliberately a *subset* of ORM/CSDP: it carries exactly what
  Rmap consumes now. A future consumer needing more (subtype totality, set
  constraints, derived facts) extends the block, gated as a new decision.
- The reference `LoginSchemas` loader resolves the repository root from the
  working directory; an app derived from the seed rebinds it to its own
  `<Name>.data-model.md` files (the failure message names this).
- Rollback: revert the branch; the `## State` input path is retained.
