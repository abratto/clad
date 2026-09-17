# Maintenance change — `spec-renamed-to-concept-contract`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + generators + templates + docs + the worked example)
- **Feature-contract impact:** `re-entered`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** What CLAD called a **SPEC** is renamed everywhere to the **concept contract** — the artefact `<Name>.spec.md` → `<Name>.contract.md`, the stage folder `04b_spec/` → `04b_contract/`, the stage label, the generator and parity script, and the prose. It is also made **canonical** (a corpus artefact beside the concept), so an extending feature moves it and a reusing feature binds it.

## Why

Two problems, found while extending concepts for the first time (the
library-lending experiment's UC-03):

1. **The name did not say what it is.** Its own template says it is "the
   **contract slice of a concept that the implementation compiles against**",
   and `ARTEFACT_MAP.md` adds that "all inner-loop and outer-loop tests
   reference [it], not prose". It is a derived, compilation-facing contract —
   but CLAD called four different things "spec": the *concept spec*
   (`<Name>.concept.md`), the *sync spec* (`<name>.sync.md`), the *SPEC*
   (`<Name>.spec.md`), and the *port spec*. `SPEC` is also not an acronym.
2. **It was per-UC, so it drifted.** A feature extending a concept produced a
   second, divergent contract for it (UC-03's `MemberEnrolment` would carry
   `verify` while UC-01's carried only `enrol`), leaving the introducer's copy
   stale and unflagged. This is the same drift the concept-owned data model
   change (`concept-owned-data-model`) fixed one stage over.

## Rule

- The artefact is `<Name>.contract.md`; the stage is **04b — Concept contract**
  (folder `04_implement/04b_contract/`); the generator is
  `generate_contract.py`; the parity gate is `verify_contract_parity.py`.
- The canonical contract lives at
  `features/_system/concepts/<Name>.contract.md`, promoted with the spec and
  the data model.
- A feature derives a contract only for a concept it **introduces or extends**
  (an extend moves the action surface); a `reused` concept binds the canonical
  contract. A legacy map with no `Origin` keeps one contract per concept.
- A contract's outcome enums come from the **concept's own flow tokens**, unioned
  with the feature's approved chain outcomes — never from the chain alone: a
  feature that only extends a concept does not invoke its older actions, so a
  chain-derived enum would silently drop them (UC-03 lost `enrol`'s and
  `acquire`'s).
- `port-spec.md` (the external adapter contract) is unaffected; `contract.py`,
  the feature-descriptor identifier module, is renamed `descriptor.py` to
  remove the collision.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No action, outcome, or token changes; only names and locations |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — |
| Gate scripts | yes | `clad_stages.py` (stage, checks, `_CONTRACT_PARITY`, `_CONTRACT_MANIFEST`, `feature_contract_concepts`), `artifact_parsers` (`feature_contract_concepts`, `04b` manifest, `parse_spec_*` → contract dir), `generate_spec.py` → `generate_contract.py`, `verify_spec_parity.py` → `verify_contract_parity.py`, `--spec-dir` → `--contract-dir` across the checker family, `present_gate.py`, `contract.py` → `descriptor.py` |
| Gate tests | yes | every test referencing the artefact, the scripts, or the flag |
| Templates | yes | `templates/spec.md` → `templates/contract.md`; the skeleton `04b_spec/` → `04b_contract/` and its CONTEXT |
| Methodology docs | yes | STAGES, ARTEFACT_MAP, TRACEABILITY, CONCEPTS, TDD, QUALITY_GATE, FLOW_TOKENS, ORIGINS, WALKTHROUGH, RULES, GHERKIN_INTEGRATION, MENTAL_MODEL, DELIVERY, PORTS_AND_ADAPTERS, WEB_CONCEPT, CONTRACTS |
| Skills | yes | `clad-spec-extraction` prose and the stages it names |
| Corpus | yes | `<Name>.contract.md` beside each canonical spec |
| UC-00 artefacts | yes | 04b folder + three artefacts renamed (Gate 3 re-approval) |
| Experiment features | yes | UC-01, UC-02, UC-03 04b renamed (Gate 3 re-approval each) |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| A reused concept's contract is not re-derived | unit | `test_concept_registry.py::test_contract_is_not_rederived_for_a_reused_concept` | pass | — |
| An extend derives the contract | unit | `…test_contract_is_derived_for_an_extend` | pass | — |
| Promotion carries the contract and stays idempotent | unit | `…test_promotion_carries_the_conceptual_data_model` (companions) | pass | — |
| Legacy map keeps one contract per concept | unit | `expected_stage_outputs(UC-00)["04b"]` = 3 | pass | — |
| Pipeline + sequence intact | integration | `verify_artefacts.py`; `verify_stage_sequence --through 05` | pass | after Gate 3 re-approval |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 152 passed |
| Reactor intact | integration | `mvn -q test -f reference-impl/pom.xml -pl java-legible -am` | pass | exit 0 |

## Gates

### Design gate

Approved in-conversation: "full rename, including scripts and folder", plus
making the contract canonical.

### Evidence gate

To be recorded before commit.

## Notes

- Mechanical rename of a derived artefact: no action, outcome, sync, or flow
  token changes, so behaviour is preserved; the gate re-approvals exist because
  the 04b `output/` content changed.
- The iterative-change matrix row label `SPEC slices` became `Contract slices`
  (the row is a schema identifier the readiness check requires).
