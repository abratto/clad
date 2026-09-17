# Maintenance change — `concept-owned-data-model`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + generators + corpus + docs)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** The **conceptual data model becomes a canonical artefact of the concept**, living beside its spec at `features/_system/concepts/<Name>.data-model.md`. A feature derives one only when it introduces or changes the concept's state; a reused concept binds the canonical model.

## Why (experiment-found)

Under the system-scope concept model the concept's *state* is canonical, so its
CSDP data model is canonical too — but `03b` derived one for **every concept the
use case uses**. On UC-03 (`borrow-copy`) that produced a second
`MemberEnrolment.data-model.md` and a second `Stocking.data-model.md`, duplicating
UC-01's and UC-02's. Nothing compares per-feature data models, so the copies
could drift silently — the same failure mode Model B removed for concept specs
(the Conduit rebuild's six divergent `Session.concept.md`).

The workaround applied in the moment — copying the introducer's model verbatim —
proved the point: if the two must be identical, there should be one.

## Rule

- The canonical model is `features/_system/concepts/<Name>.data-model.md`,
  promoted with the spec (`./clad promote-concepts` copies both).
- A feature derives a model **only** for a concept it introduces (`new`) or
  whose `## State` it changes (an `extends:` whose state block differs from the
  canonical spec). A `reused` concept, or an extend that leaves state untouched
  (UC-03's `verify`/`lend`), binds the canonical model — no copy.
- A map with no `Origin` column (pre-Model-B) keeps the old expectation: one
  model per concept.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No concept or sync content changes |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — |
| Gate scripts | yes | `artifact_parsers.feature_model_concepts` (single source of truth) + `expected_stage_outputs["03b"]`; `clad_stages.feature_model_concepts` delegates; `generate_data_model.py` filters; `promote_concepts.py` promotes the model |
| Gate tests | yes | reused / state-preserving-extend / promotion-carries-model cases |
| Methodology docs | yes | `CONCEPTS.md`, `ARTEFACT_MAP.md`, `TRACEABILITY.md`, `STAGES.md` |
| Corpus | yes | `<Name>.data-model.md` added beside each canonical spec |
| UC artefact chain | no | UC-00's and the experiment's outputs are already shaped this way; no stage is re-derived |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| A reused concept is not re-derived | unit | `test_concept_registry.py::test_data_model_is_not_rederived_for_a_reused_concept` | pass | — |
| A state-preserving extend is not re-derived | unit | `…test_data_model_is_not_rederived_for_a_state_preserving_extend` | pass | — |
| A `new` concept is derived, corpus concepts are not | unit | `…test_per_uc_generator_emits_only_the_features_concepts` | pass | — |
| Promotion carries the model and stays idempotent | unit | `…test_promotion_carries_the_conceptual_data_model` | pass | — |
| Legacy (no `Origin`) keeps one model per concept | unit | `expected_stage_outputs(UC-00)["03b"]` = 3 | pass | — |
| Pipeline + sequence intact | integration | `verify_artefacts.py`; `verify_stage_sequence --through 05` | pass | intact |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 149 passed |
| Reactor intact | integration | `mvn -q test -f reference-impl/pom.xml -pl java-legible -am` | pass | exit 0 |

## Gates

### Design gate

Approved in-conversation: option 1 — hoist the conceptual data model to the
canonical concept, symmetric with the concept spec.

### Evidence gate

To be recorded before commit.

## Notes

- Symmetric with D2 ("the corpus IS the canonical spec"): the model is derived
  from the canonical state, so it is canonical as well.
- Follow-up not taken here: 04b's SPECs have the same shape question — a
  feature produces a SPEC for a reused concept too. SPECs are per-profile
  compilation inputs rather than derived views, so they were left as they are;
  worth revisiting if a profile ever compiles a reused concept twice.
