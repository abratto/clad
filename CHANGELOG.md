# Changelog

All notable changes to this repository will be documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches 1.0.

Pre-1.0 minor versions can include incompatible methodology changes; the
file `methodology/` is the source of truth for what each version contains.

## [Unreleased]

### Methodology

- **Gherkin/Cucumber BDD track (optional outer-red flow tests)**: Stage
  04c can now mechanically derive executable Gherkin `.feature` files and
  step-definition skeletons from upstream CLAD artefacts (usecase.md,
  chain tables, SPECs, sync specs), replacing hand-written markdown flow
  specs with executable specifications that go green at the end of 04e.
  The track is profile-optional — set `TEST_FRAMEWORK=CUCUMBER` in
  `_config/test-framework.md` to opt in. Includes a comprehensive
  reference at `methodology/architecture/GHERKIN_INTEGRATION.md` with
  structured derivation rules (G1–G5, S1–S3, E1), cross-stage
  consistency checks, and a worked example in the Java reference profile.
  See also `templates/feature.feature` and `templates/step-definitions.java`.
- **Deterministic cross-stage verification scripts**: Added a suite of
  7 profile-agnostic Python scripts under `quality-gate/` that automate
  the cross-stage consistency checks previously done by non-deterministic
  LLM self-audit. Each script replaces a manual "did the LLM remember to
  check this?" step with a pass/fail command. Checks include file manifest
  integrity (`verify_file_manifest.py`), scenario coverage
  (`verify_scenario_coverage.py`), outcome alignment
  (`verify_outcome_alignment.py`), action chain consistency
  (`verify_action_chain.py`), sync contract matrix completeness
  (`verify_sync_matrix.py`), CSDP data-model structure
  (`verify_data_model.py`), and SPEC parity (`verify_spec_parity.py`).
  Stage CONTEXT templates updated to invoke these scripts in their
  `## Verify` sections alongside the remaining semantic (human) checks.
- **ArchUnit extensions**: Added two new heuristic checks to
  `LegibleArchitectureRulesTest`: R5 action token emission (verifies
  every concept action handler calls `writeCompletion`/`writeError`) and
  R4 controller boundary (non-Web, non-Debug infrastructure classes must
  not depend on concept or sync packages).

- **Stage 03b CSDP fidelity**: Restored the conceptual data-model walk
  to Halpin's explicit seven-step CSDP, added a dedicated
  `templates/data-model.md`, and updated the UC-00 worked example to
  show the fuller step-by-step structure.
- **Web boundary hardening**: Tightened Stage 04 and Stage 05 so
  bootstrap / `Web` implementations must prove transport-only
  behaviour, and added a Java-profile architecture test forbidding
  `Web` infrastructure classes from depending directly on business
  concept packages.
- **Web branching heuristic**: Added a Java-profile source-level check
  that rejects imperative branching in `Web` infrastructure code unless
  a transport-only exception is marked explicitly.
- **Sync orchestration hardening**: Tightened Stage `04e` to treat
  imperative coordinator/orchestrator code as a defect, and added
  Java-profile checks that sync package classes use `SyncAgent`, reject
  imperative branching in sync source by default, and ban
  `*Coordinator` / `*Orchestrator` classes unless explicitly waived.
- **Action-chain test contract**: Tightened Stage `04c` / `04e` so each
  scenario must name an expected authored action chain and green status
  must be explained against that chain, not only against the final HTTP
  response.
- **Implementation derivation order**: Tightened `04d` / `04e` so code
  is derived first from approved upstream artefacts and uses the
  Java/Jena/Micronaut example only as a profile realization pattern.
- **Reference-profile copy-out rule**: Clarified that repositories
  created from the CLAD template should treat `reference-impl/` as a
  clean upstream exemplar and copy chosen starter profiles into their
  real app root instead of mixing product code into the reference tree.
- **Java package-placement contract**: Tightened the Java profile docs
  and Stage `04d` / `04e` contracts so agents place DTOs, transport,
  engine classes, concepts, syncs, and flow tests in the canonical
  Java subpackages instead of ad hoc siblings.
- **Java package-placement enforcement**: Added ArchUnit checks so
  concrete `*Concept` classes must live under `concepts.<name>` and
  executable `SyncAgent` implementations must live under `syncs`.
- **Java `api` / `engine` placement enforcement**: Added ArchUnit
  checks so Micronaut boundary DTOs live under `api` and the canonical
  runtime abstractions stay under `engine`.
- **Java OpenAPI starter support**: Added Micronaut OpenAPI generation,
  Swagger UI exposure, boundary-level OpenAPI annotations for the login
  example, and guidance that generated transport docs remain subordinate
  to CLAD's upstream artefacts.

## [0.2.0] — 2026-05-12

### Methodology

- **RESUME rule** (rule 9 in `AGENTS.md`): Mandatory state artefact
  (`features/UC-XX-<slug>/RESUME.md`) at every stage gate, capturing last
  completed stage, gate outcome, corrections, deferred concepts, next stage,
  next task. Templates at `templates/feature-skeleton/RESUME.md`.
- **Testing discipline** (rule 8): Tests precede implementation. Added
  `TDD.md` documenting the London School outside-in double-loop (04c flow
  tests → 04d concept TDD → 04e sync TDD). Pre-condition tables added to
  04_implement router to enforce gate verification before advancing.
- **Bootstrap concept generalisation**: Clarified that Web is one example
  (via 04b `Inputs` contract); other concepts can be bootstrap points if
  justified in Stage 02a.
- **Sync authoring refinements**: Added "DECLARE BEFORE USE" rule,
  then-only rule clarifications, and syncs must emit flow tokens explicitly.
- **Branch and commit hygiene** (`DELIVERY.md`): Rule 7 (branch creation)
  and rule 8 (commit messages) documented; RESUME.md written before each
  commit.
- **Handover protocol** (`methodology/implementation/HANDOVER.md`): New
  stage-entry orientation artefact for agents joining in-flight features.
  Specifies strict read order (AGENTS.md → STAGES.md → DELIVERY.md →
  HANDOVER.md → templates → stage outputs → RESUME.md).

### Documentation

- **Concept templates**: Adopted Alloy-style notation in concept state
  definitions; restructured derivation map to group tests by action with
  one class per action. Added outcome-alignment contract to Stage 02
  CONTEXT.
- **ORM_NOTES**: Revised Step 7 to enforce profile-neutral conceptual
  models (RDF triple facts independent of storage layer).
- **Usecase template**: Added worked Cockburn-format extensions example;
  added scenario-vs-extension and identical-postconditions guidance
  (`templates/usecase.md`).
- **FLOW_TOKENS.md**: Added casing convention (SCREAMING_SNAKE_CASE),
  one-token-per-invocation rule (never batch events), and payload
  prohibitions (no nested objects).
- **CSDP reduction**: Simplified ORM derivation from seven to six steps;
  added post-walk profile mapping note section.
- **Dependency review card** (`03a` template): Clarified then-only rule
  and cross-concept coupling surface patterns.
- **Agent capability profiles** (`AGENTS.md`): Mapped stage groups to
  required reasoning depth (prose synthesis, deep structural reasoning,
  code generation, audit/traceability).

### Tooling & CI

- **Roo Code integration**: Added `.roorules-clad-architect` for stages
  00–03 and 05; `.roorules-clad-red` for 04c flow tests; `.roorules-clad-green`
  for 04d/04e TDD. Modes cover full outside-in loop.
- **Roo configuration**: Added `.roo-clad-config.example` for
  per-developer mode switching; `.roo-clad-config` (local, gitignored)
  enables developer customization.
- **fileRegex expansions**: Expanded clad-architect and clad-red patterns
  to match stage letter suffixes (02a, 02b, 03a, etc.) and flow-test specs
  / derivation maps.
- **Feature skeleton hook**: Added `_config` file to `templates/feature-skeleton/`
  documenting canonical build/test command per project type.

### Templates

- **Test intent derivation**: Updated 04d template to require pre-04c
  verification; Preconditions column and reasoning bullets added.
- **Sync template**: Updated pattern labels for clarity; added DECLARE
  BEFORE USE guidance.

### Verification & Checks

- **Repeated-action checks**: Added backstop cross-stage check (02b→03
  Verify section) and repeated-action-invocation check (02b Verify) to
  catch unintended action duplication.
- **Pre-condition framework**: 04_implement router now verifies that each
  sub-stage gate output is present and valid before advancing (04c→04d,
  04d→04e).
- **Build/test evidence**: 04e gate now requires executed test evidence
  for true red and green states (not just staged files).

### Fixes

- Chain-table diagram type corrected to `stateDiagram-v2` (was
  `sequenceDiagram`).
- Merge conflict resolution: rule 9, DELIVERY.md §3, HANDOVER.md content
  standardized across PR #20 and PR #21 consolidation.

### Notes

This release rolls up ~70 commits over 5 days of methodology refinement,
driven by second-pass walkthroughs on Stage 02–05 and Roo Code tooling
integration. The RESUME artefact and TDD discipline are now mandatory
(hard rules). Syncs are now stricter (declarative-only, must emit tokens).
Ready for Round-12+ feature work.

## [0.1.0] — 2026-05-07

Initial public seed.

### Methodology

- **CLAD core** (`methodology/core/`): `CLAD.md`, `CONTRACTS.md`,
  `ARTEFACTS.md`, `ITERATIVE_CHANGES.md`.
- **Legible / WYSIWID architecture** (`methodology/architecture/`):
  `LEGIBLE.md`, `CONCEPTS.md`, `SYNCHRONIZATIONS.md`, `SYNC_PATTERNS.md`,
  `WEB_CONCEPT.md`, `ENGINE.md`, `MENTAL_MODEL.md`, `ARTEFACT_MAP.md`,
  `FLOW_TOKENS.md`, `DATA_MODEL_NOTES.md`.
- **ICM implementation** (`methodology/implementation/`): `STAGES.md`
  (00 → 05 with 04a–04e sub-stages), `RULES.md` (the five hard rules),
  `STORAGE_MAPPING.md`, `QUALITY_GATE.md` (local pre-commit),
  `DELIVERY.md` (trunk-based + CI gate).
- **Optional overlays** (`methodology/overlays/`): `TRACKING.md` and
  `DECISIONS.md`.
- **Worked example**: `features/UC-00-login/` taken end-to-end through
  Stage 04 (Stage 05 closure pending). Annotated session walkthrough at
  `methodology/WALKTHROUGH.md`.

### Repository scaffold

- Canonical agent guide at `AGENTS.md`; thin adapters at `CLAUDE.md`,
  `.github/copilot-instructions.md`, `.cursor/rules/clad.mdc`.
- Workspace router at `CONTEXT.md`.
- Templates at `templates/` (incl. `templates/feature-skeleton/` for
  bootstrapping new features).
- Optional Java profile at `reference-impl/java-micronaut-jena/`.

### Tracking overlay

- Seeded `ROADMAP.md` at repo root (CI-checked, opt-out by deletion).
- "After cloning" one-time-setup checklist in `CONTRIBUTING.md`.

### CI

GitHub Actions workflow `.github/workflows/ci.yml` with four jobs:

- `markdown-links` — link check across all `*.md`.
- `hard-rule-r1` — bash grep enforcing R1 (no cross-concept imports)
  across `reference-impl/**/*.java`.
- `tracking-hygiene` — enforces `ROADMAP.md` conventions (≤1 `doing`
  row; resume point present; `Last updated` no older than 60 days).
- `java-verify` — conditional `mvn verify` when the Java profile's
  `pom.xml` is present.

### Notes

This release is the **seed** — usable as a `Use this template`
starter. The broader reference implementation lives at
[`abratto/tastetag`](https://github.com/abratto/tastetag) (private)
and will be ported into `reference-impl/` over subsequent releases.

[Unreleased]: https://github.com/abratto/clad/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/abratto/clad/releases/tag/v0.1.0
