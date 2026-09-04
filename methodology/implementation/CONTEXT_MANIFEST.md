# CONTEXT_MANIFEST.md — per-stage file manifest

> Machine-readable map of what a generic agent must load for each CLAD
> stage. **Derived from each stage's `CONTEXT.md`**, never invented
> independently. If a row here disagrees with a stage `CONTEXT.md`, the
> `CONTEXT.md` is authoritative — fix this table, not the contract.
>
> Column legend:
> - **Required** — files/sections the stage `Inputs` table names; a
>   generic agent must load exactly these.
> - **Conditional** — files loaded only when the stated condition holds
>   (e.g. an external port spec exists, or a non-default profile is
>   selected).
> - **Excluded** — categories the stage must NOT load (future-stage or
>   unrelated material).
> - **Outputs** — the closed list the stage writes.
> - **Verify** — the pass/fail self-audit command(s) before the gate.
> - **Gate** — human gate (`G0`/`G1`/`G2`/`G3`) or auto-advance.
> - **Profile** — profile assumption for that stage.

## Stage 00 — actor/goal (system scope)

| Field | Value |
|---|---|
| Required | human brief; `templates/actors.md`; `templates/goals.md`; `methodology/implementation/STAGES.md` §"Scope" |
| Conditional | `templates/port-spec.md` (only when an external adapter contract exists) |
| Excluded | all per-UC stage CONTEXT.md files; templates for concept/sync/data-model |
| Outputs | `actors.md`, `goals.md`, optional `port-spec.md` |
| Verify | actors↔goals cross-check; out-of-scope non-empty; forward goal count |
| Gate | **G0** (system-level, multi-turn) |
| Profile | profile-agnostic |

## Stage 01 — use case

| Field | Value |
|---|---|
| Required | `00_actor-goal/output/actors.md`; `goals.md`; `methodology/core/CLAD.md`; `templates/usecase.md`; `_config/voice.md` |
| Conditional | `port-spec.md` (external adapter contract) |
| Excluded | responsibility-map/chain/sync/data-model templates; implementation files |
| Outputs | `usecase.md` |
| Verify | `verify_file_manifest.py` + semantic checks |
| Gate | auto → 01b |
| Profile | profile-agnostic |

## Stage 01a — responsibility map

| Field | Value |
|---|---|
| Required | `01_usecase/output/usecase.md`; `00_actor-goal/output/actors.md`; `methodology/architecture/CONCEPTS.md`; `methodology/implementation/RULES.md` (R1); `templates/responsibility-map.md` |
| Conditional | — |
| Excluded | sync/data-model/implementation material |
| Outputs | `responsibility-map.md` |
| Verify | `verify_file_manifest.py` + semantic coverage checks |
| Gate | auto → 01b |
| Profile | profile-agnostic |

## Stage 01b — chain table

| Field | Value |
|---|---|
| Required | `01_usecase/output/usecase.md`; `01a_responsibility-map/output/responsibility-map.md`; `methodology/architecture/SYNCHRONIZATIONS.md`; `templates/chain-table.md` |
| Conditional | — |
| Excluded | concept spec, sync spec, implementation material |
| Outputs | `<scenario>-chain.md` (one per scenario) |
| Verify | `verify_file_manifest.py` + present_gate.py |
| Gate | **G1 (Requirements)** |
| Profile | profile-agnostic |

## Stage 02 — concepts

| Field | Value |
|---|---|
| Required | `01_usecase/output/usecase.md`; `01a_responsibility-map/output/responsibility-map.md`; `01b_chain-table/output/`; `00_actor-goal/output/actors.md`; `methodology/architecture/CONCEPTS.md`; `methodology/implementation/RULES.md` (R1, R2); `templates/concept.md` |
| Conditional | — |
| Excluded | sync spec, data-model, implementation material |
| Outputs | `<Name>.concept.md` (one per business concept) |
| Verify | `verify_action_chain.py`; `verify_file_manifest.py` |
| Gate | auto → 03b |
| Profile | profile-agnostic |

## Stage 03 — syncs

| Field | Value |
|---|---|
| Required | `01_usecase/output/usecase.md`; `02_concepts/output/`; `01b_chain-table/output/`; `methodology/architecture/SYNCHRONIZATIONS.md` (sync semantics); `methodology/architecture/SYNC_PATTERNS.md` (A/B/C/D); `methodology/implementation/RULES.md` (R3); `templates/sync.md` |
| Conditional | — |
| Excluded | data-model, SPEC, implementation material (do not pre-author `04e` lowering) |
| Outputs | `<name>.sync.md` (one per rule); optional `<scenario>-sync-summary.md` |
| Verify | `verify_sync_matrix.py`; `verify_scenario_coverage.py`; `verify_file_manifest.py` |
| Gate | auto → 03b |
| Profile | profile-agnostic |

## Stage 03a — dependency review

| Field | Value |
|---|---|
| Required | `03_syncs/output/`; `01b_chain-table/output/`; `01a_responsibility-map/output/responsibility-map.md`; `02_concepts/output/`; `methodology/architecture/SYNC_PATTERNS.md`; `templates/dependency-review-card.md`; `templates/pattern-d-summary.md` |
| Conditional | — |
| Excluded | data-model, implementation material |
| Outputs | `<concept>-card.md` (one per concept); `pattern-d-summary.md`; `concept-matrix.md` |
| Verify | `verify_file_manifest.py`; `verify_sync_route_filters.py` |
| Gate | auto → 03b |
| Profile | profile-agnostic |

## Stage 03b — data model

| Field | Value |
|---|---|
| Required | `02_concepts/output/`; `03a_dependency-review/output/pattern-d-summary.md`; `methodology/architecture/DATA_MODEL_NOTES.md`; `methodology/implementation/RULES.md` (R1, R2); `templates/data-model.md` |
| Conditional | — |
| Excluded | storage mapping, SPEC, implementation material |
| Outputs | `<Name>.data-model.md` (one per concept) |
| Verify | `verify_data_model.py`; `verify_file_manifest.py` |
| Gate | **G2 (Architecture)** |
| Profile | profile-agnostic (profile-neutral models) |

## Stage 04a — storage mapping

| Field | Value |
|---|---|
| Required | `03b_data-model/output/`; `_config/package-and-layout.md`; `methodology/implementation/RULES.md` (R2); `methodology/implementation/STORAGE_MAPPING.md`; `templates/storage.md` |
| Conditional | profile reference docs (e.g. `reference-impl/<profile>/README.md`) — only when a persistent profile is selected |
| Excluded | SPEC/flow test/concept-sync implementation material |
| Outputs | `<Name>.storage.md` per concept **or** `_NOT_APPLICABLE.md` (in-memory profile) |
| Verify | `verify_file_manifest.py` |
| Gate | auto → 04c |
| Profile | default = in-memory `FactStore` (`java-legible`); legacy Jena/Postgres conditional |

## Stage 04b — SPEC

| Field | Value |
|---|---|
| Required | `02_concepts/output/`; `templates/spec.md` |
| Conditional | `00_actor-goal/output/port-spec.md` (external adapter contract) |
| Excluded | flow test/implementation material |
| Outputs | `<Name>.spec.md` per concept |
| Verify | `verify_spec_parity.py`; `verify_file_manifest.py`; `verify_port_spec_contract.py` |
| Gate | auto → 04c |
| Profile | profile-agnostic |

## Stage 04c — flow tests (outer red)

| Field | Value |
|---|---|
| Required | `01_usecase/output/usecase.md`; `01b_chain-table/output/`; `03_syncs/output/`; `04b_spec/output/`; `_config/build-and-test.md`; `_config/package-and-layout.md`; `methodology/architecture/FLOW_TOKENS.md`; `methodology/implementation/TDD.md`; `templates/feature.feature`; `templates/step-definitions.java` |
| Conditional | `00_actor-goal/output/port-spec.md` (`@contract` scenarios) |
| Excluded | concept/sync green implementation (red phase: tests only) |
| Outputs | `<feature-name>.feature`; step-definition skeleton; Cucumber runner |
| Verify | `verify_feature_file_presence.py`; `verify_file_manifest.py`; `verify_gherkin_derivation.py`; `verify_step_definition_parity.py`; `verify_step_definition_derivation.py`; `verify_port_spec_contract.py` |
| Gate | **G3 (Executable)** |
| Profile | profile-specific test setup, chosen profile's build-and-test |

## Stage 04d-red — concept test derivation

| Field | Value |
|---|---|
| Required | `02_concepts/output/`; `04b_spec/output/`; `04c_flow-tests/output/`; `_config/build-and-test.md`; `_config/package-and-layout.md`; `templates/test-intent-derivation-map.md`; `methodology/implementation/RULES.md` (R1, R5, R14, R16); `methodology/implementation/TDD.md` |
| Conditional | profile conventions (`reference-impl/java-legible/` default; `java-micronaut-jena/` legacy only) |
| Excluded | green implementation code (tests only) |
| Outputs | `concept-test-derivation.md` + test files |
| Verify | `verify_file_manifest.py`; `verify_concept_test_derivation.py`; `verify_concept_field_assertions.py`; `verify_test_naming.py` |
| Gate | auto → 04d-green |
| Profile | default `java-legible`; legacy Jena conditional |

## Stage 04d-green — concept implementation

| Field | Value |
|---|---|
| Required | `02_concepts/output/`; `04a_storage-mapping/output/`; `04b_spec/output/`; `04d_red-tests/output/`; `_config/build-and-test.md`; `_config/package-and-layout.md`; `methodology/implementation/RULES.md` (R1, R5, R8, R9, R14, R16); `methodology/implementation/TDD.md` |
| Conditional | profile conventions (`java-legible` default; `java-micronaut-jena` legacy only) |
| Excluded | sync implementation (belongs in 04e) |
| Outputs | `<Name>Concept.java` + green tests (side effects) |
| Verify | green tests; field-value assertions; iterative-change coupling |
| Gate | auto → 04e-red |
| Profile | default `java-legible`; legacy Jena conditional |

## Stage 04e-red — sync test derivation

| Field | Value |
|---|---|
| Required | `03_syncs/output/`; `04b_spec/output/`; `04c_flow-tests/output/`; `04d_concept-tdd/04d_red-tests/output/`; `_config/build-and-test.md`; `_config/package-and-layout.md`; `templates/test-intent-derivation-map.md`; `methodology/implementation/RULES.md` (R3); `methodology/implementation/TDD.md` |
| Conditional | profile conventions (`java-legible` default; `java-micronaut-jena` legacy only) |
| Excluded | green sync implementation (tests only) |
| Outputs | `sync-test-derivation.md` + test files |
| Verify | `verify_file_manifest.py`; `verify_test_naming.py` |
| Gate | auto → 04e-green |
| Profile | default `java-legible`; legacy Jena conditional |

## Stage 04e-green — sync implementation

| Field | Value |
|---|---|
| Required | `03_syncs/output/`; `04b_spec/output/`; `04c_flow-tests/output/`; `04e_red-tests/output/`; `_config/build-and-test.md`; `_config/package-and-layout.md`; `methodology/implementation/RULES.md` (R3); `methodology/implementation/TDD.md` |
| Conditional | profile lowering contract (`SYNC_LOWERING.md` — Java/Jena/Micronaut legacy only); `java-legible` default |
| Excluded | new syncs, coordinator classes (declarative only) |
| Outputs | `green-evidence.md`; `<SyncName>.java` + green tests |
| Verify | `verify_cucumber_green.py`; `verify_implementation_parity.py`; `verify_sync_implementation_parity.py` |
| Gate | auto → 05 |
| Profile | default `java-legible`; legacy Jena conditional |

## Stage 05 — verify + close

| Field | Value |
|---|---|
| Required | `01_usecase/output/usecase.md`; `03_syncs/output/`; `04_implement/output/implementation-manifest.md`; runtime flow-token log; `methodology/architecture/FLOW_TOKENS.md` |
| Conditional | `reference-impl/<profile>/README.md` (selected profile's runtime debug surface) |
| Excluded | any downstream material (this is the final stage) |
| Outputs | `trace.md`; `findings.md`; `smoke.md`; `tracking.md` |
| Verify | back-trace every token to a scenario; smoke run; Gherkin coverage |
| Gate | auto (close) |
| Profile | selected profile's runtime debug surface (default `java-legible`; legacy Jena conditional) |

---

## Maintenance route (engine/profile/config/deployment changes)

Not a stage — the routing table for work that preserves the feature
contract. See `methodology/core/ITERATIVE_CHANGES.md` §"Platform
maintenance changes" and `templates/maintenance-change.md`. Route:
`maintenance/<change-name>.md`, design gate → implement → evidence gate.
Governed by R20 and `verify_maintenance_change_readiness.py`.
