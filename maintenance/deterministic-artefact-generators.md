<!-- Maintenance-route planning record. -->
# Maintenance change — `deterministic-artefact-generators`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles` (quality-gate is profile-agnostic)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Add deterministic generators for the mechanically-derivable CLAD stages (03 syncs, 03a dependency cards, 03b data models, 04b SPECs, 04c Gherkin scaffolds) plus a shared artefact-parser layer, so a weak local model can run those stages via scripts instead of LLM authoring.

## Why

CLAD's verification side is already deterministic (33 `verify_*.py` scripts), but
several stages still have the LLM *author* what is actually a mechanical
transformation, then a script merely checks it after the fact. On a weak local
model this "generate-then-verify" loop produces subtle byte-level errors that a
human must catch at the gate. The stages whose outputs are pure functions of
prior artefacts + rules — **03 (syncs)**, **03a (dependency cards)**, **04b
(SPECs)** — should be *generated deterministically*, with the LLM resolving only
the genuinely non-derivable parts (Pattern D concept-state reads, `where`
sources, type/flow-token transcription). This shift gives strong quality
guarantees exactly where a weak model is least reliable, while reserving the
model for the irreducibly-judgment stages (00 collaborative intake, 01 prose,
01a concept decomposition, 02 concept design).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Generators emit, they do not decide; names/matrix/trigger/target are derived from approved chain tables + concepts. |
| Action ordering and sync deduplication | preserved | One sync per chain-table transition, deduped by stem; firing order is declaration order (unchanged engine behaviour). |
| Flow-token lineage | preserved | No runtime surface change. |
| Storage/retention semantics | preserved | No `FactStore`/`Region`/archiver change. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `methodology/implementation/STAGES.md`, `AGENTS.md` (new "deterministic generation vs authoring" note); `ORIGINS.md` unchanged. |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Profile tests | yes | New `quality-gate/tests/test_generators.py` (4 property tests). |
| UC artefact chain | no | Generators reproduce the same artefact shape/semantics; no `.concept.md`/`.sync.md` contract change. |

## Migration of the verify scripts (parser extraction)

Five checks were refactored to import shared parsers from
`quality-gate/artifact_parsers.py`, with behaviour preserved
(verified: identical parser output across all UC-00-login artefacts):

- `verify_action_chain.py`
- `verify_outcome_alignment.py`
- `verify_scenario_coverage.py`
- `verify_spec_parity.py`
- `verify_sync_cycle_graph.py`

The shared parsers (`parse_chain_table`, `parse_concept`, `parse_sync`,
`parse_responsibility_map`, `parse_spec_outcomes`, naming helpers
`pascal_token`/`first_completion_token`/`feature_scope_from_path`) are the
single grammar source for both checks and generators, so the two cannot drift.

## New generators

| Script | Stage | Produces | Flags for LLM |
|---|---|---|---|
| `generate_syncs.py` | 03 | one `*.sync.md` per chain transition (matrix, compressed-rule name, `when`/`then` skeleton, A/B/C bindings) | Pattern D reads, `then` args, `where` sources |
| `generate_sync_cards.py` | 03a | one `*-card.md` per concept + `pattern-d-summary.md` | `<args>`/`<source>`/`<field>`/`<id>`/`<scenario>` fills |
| `generate_data_model.py` | 03b | one `<Name>.data-model.md` per concept — 7-step CSDP skeleton; Object/Fact types + uniqueness/mandatory auto-derived from `-- mandatory`/`-- optional`/`-- unique` state annotations | Steps 1 (examples/facts), 3 (combination/derivations), 6 (value/subtype), 7 (final checks) |
| `generate_spec.py` | 04b | one `<Name>.spec.md` per business concept (Web excluded) | input types, flow-token shape |
| `generate_feature_files.py` | 04c | the `.feature` scaffold — Feature header, one Scenario stub per use-case scenario, terminal status + token-chain comment derived from chain tables | `Given`/`When`/body-shape prose, `I want`/`So that` wording, Scenario Outline `Examples:` |

Each is manual-first: the stage CONTEXT instructs "run the generator, then
resolve only the TODO markers." Generators are never auto-run by `advance.py`
(this change keeps them a deliberate, reviewable step).

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Sync generator reproduces canonical names | unit | `test_generate_syncs_reproduces_canonical_names` | pass | 7 stems match UC-00-login exactly |
| Generated syncs pass the Stage 03 checks | unit/property | `test_generated_syncs_pass_sync_checks` (runs `verify_sync_matrix`/`verify_sync_cycle_graph`/`verify_sync_overlap` on generator output) | pass | all exit 0 |
| SPEC generator excludes bootstrap + covers concepts | unit | `test_generate_spec_excludes_bootstrap_and_covers_concepts` | pass | PasswordAuth/Session/UserNaming |
| Card generator covers participating concepts incl. Web | unit | `test_generate_cards_cover_participating_concepts` | pass | 4 cards + pattern-d-summary |
| Data-model generator passes CSDP structure check | unit/property | `test_generate_data_model_passes_csdp_structure_check` (runs `verify_data_model.py` on generator output) | pass | 3 models, structure-check exit 0 |
| Feature generator derives scenarios + status codes | unit | `test_generate_feature_files_derives_scenarios_and_status` | pass | 4 scenarios, 200/401 statuses |
| Refactored verify scripts unchanged | unit | full `quality-gate/tests` suite (44 tests) | pass | 44/44 |
| Artefact pipeline gate intact | gate | `python3 quality-gate/verify_artefacts.py` | pass | exit 0 |

## Gates

### Design gate

Review contract impact, the parser-extraction (behaviour-preserving) claim, the
three generators' "skeleton + TODO" scope, and the manual-first decision.
Approve with `./clad approve-maintenance deterministic-artefact-generators design`.

### Evidence gate

Review the completed test matrix. Approve with
`./clad approve-maintenance deterministic-artefact-generators evidence`, then
set Status to `closed`.

## Notes

- **Deferred (explicitly out of scope this pass):** `advance.py` auto-run wiring
  (generators stay manual-first, invoked per the stage CONTEXT.md), and the
  step-definition `.java` skeleton generator for 04c (profile-specific,
  `@Disabled`; left to the agent from `templates/step-definitions.java`).
- **Pattern D remains a design judgment.** The generator auto-labels A/B/C but
  never invents a D read — consistent with the earlier decision that D is the
  only *semantic* classification a human/LLM should touch.
- **Stage 01a (concept decomposition) is intentionally NOT determinized** — it
  is the irreducibly-judgment task, per human decision.
