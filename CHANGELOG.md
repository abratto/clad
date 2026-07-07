# Changelog

All notable changes to this repository will be documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches 1.0.

Pre-1.0 minor versions can include incompatible methodology changes; the
file `methodology/` is the source of truth for what each version contains.

## [Unreleased]

### Agent Skills

- **Agent Skills standard adoption**: Added 16 portable `SKILL.md` files under
  `skills/` following the [agentskills.io](https://agentskills.io) open
  standard. Each skill maps to a CLAD stage or cross-cutting concern
  (system-scoping, usecase-authoring, chain-table, concept-design, sync-design,
  dependency-review, data-modeling, storage-mapping, spec-extraction,
  flow-testing, concept-tdd, sync-tdd, verification, handover, quality-gate).
  Skills use progressive disclosure — metadata always loaded, instructions on
  demand — and reference `methodology/` and `templates/` files by path.
- **Stage CONTEXT.md Inputs tables** now list `Skill:` entries alongside raw
  file paths. Skills-aware agents discover and load them automatically;
  non-skilled agents fall back to raw paths.
- **AGENTS.md §4b** documents the skill layer, progressive disclosure model,
  and full skill-to-stage mapping.

### Platform Integration

- **Repository governance hardening**: Added `.github/CODEOWNERS` with a
  baseline maintainer owner map and documented recommended public-template
  branch protection settings in `CONTRIBUTING.md` (PR-required merges,
  required checks, code-owner review, and restricted direct pushes).
- **Removed platform-specific rule files**: Deleted `.clinerules/` (4 Cline
  phase rules), `.roorules-clad-*` (3 Roo mode files), `.roomodes` (Roo
  config), `.cline-clad-config.example`, and `.roo-clad-config.example`.
  These were created for Roo/Cline harnesses no longer in use and contained
  outdated references (`.cline-clad-config`/`.roo-clad-config`). All unique
  guidance migrated into `AGENTS.md`, `methodology/implementation/RULES.md`,
  and `reference-impl/java-micronaut-jena/CODE_STYLE.md`.
- **README.md** "Cline setup" section replaced with platform-agnostic "Agent
  platform integration" section covering Skills and `clad.properties`.
- **TDD.md** "Phase switching in Cline" section replaced with capability
  profiles reference.
- **STAGES.md** config precedence updated from `.cline-clad-config` /
  `.roo-clad-config` to `clad.properties`.

### Methodology

- **README workflow summary**: Added a high-level "How CLAD works"
  section to `README.md` that explains the human/agent handshake,
  Stage 00 system scoping, the three per-use-case review gates, and the
  auto-advanced delivery stages in plain language.
- **Java profile scale caveat**: Updated `README.md` and
  `reference-impl/java-micronaut-jena/README.md` to state explicitly that
  the shipped Java/Micronaut/Jena reference engine is functional but has
  not yet been designed or vetted for scale; scaling work remains future
  profile-level work.
- **README implementation-profile clarification**: Updated `README.md` to
  state explicitly that CLAD is methodology-level profile-agnostic, but this
  repository currently ships only one concrete executable profile: the Java 21
  + Micronaut + Apache Jena/TDB2 reference implementation.
- **README structure and privacy cleanup**: Moved the Quick start section
  ahead of the long origin narrative so public readers reach the runnable
  path sooner, removed the public link to the private Tastetag repository,
  and kept Tastetag only as unlinked historical context in the origin story.
- **README dependency clarification**: Added a compact Requirements section
  to `README.md` that separates the minimum needs for using CLAD as a
  methodology starter from the extra dependencies for running Python
  quality-gate scripts and the optional Java 21 + Maven reference profile.
- **README public-launch framing**: Updated `README.md` to describe CLAD
  as public but pre-1.0, added a short "Who this is for" section,
  documented the pre-1.0 versioning contract explicitly, and credited
  Alan Potosnak as CLAD's author with pointers to attribution sources.
- **README quick-start onboarding refresh**: Simplified the Stage 00
  starter prompts in `README.md`, added a concrete copy-paste library
  lending brief, and turned the post-Stage-00 handoff into an exact
  prompt for creating UC folders and entering Stage 01. New users can
  now start CLAD with minimal prompt authoring while still following the
  Stage 00 contract.
- **Documentation freshness sweep**: Refreshed CLAD methodology and
  reference-profile examples after the sync naming migration. Updated
  `CANONICAL_EXEMPLAR.md`, `SYNC_LOWERING.md`, `WALKTHROUGH.md`,
  Gherkin guidance, sync-test templates, and UC-00 stage outputs so they
  match the current rule-shaped sync names, RDF-star outcome matching,
  Gherkin-only Stage 04c flow tests, and 46-test Java reference baseline.
- **R17 — Iterative-change parity rule**: Added hard rule R17 to
  `AGENTS.md §9`. Before modifying any sync or concept implementation
  file, the agent must classify the change per
  `methodology/core/ITERATIVE_CHANGES.md` and update the affected stage
  artefacts in the same commit. A class without a matching spec is a
  defect of the same severity as a cross-concept import (R1).
- **`quality-gate/verify_implementation_parity.py`**: New quality-gate
  script that mechanises R17's forward direction. For every sync
  implementation class it checks that a `*.sync.md` exists in the
  features tree; for every concept implementation class it checks that
  a `*.concept.md` exists. Triggered by diffs that touch sync or concept
  implementation source files. Added as gate check 12 in
  `methodology/implementation/QUALITY_GATE.md`.
- **Sync naming grammar**: Added canonical sync names that read as
  compressed rules:
  `When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]`.
  Stage 03 sync file stems, `sync <Name>` headers, Java class names, and
  Java `syncName()` values now lower from the same rule shape, and
  `verify_implementation_parity.py` checks this deterministically.
- **Sync implementation parity**: Added
  `quality-gate/verify_sync_implementation_parity.py` to check the opposite
  direction: every approved Stage 03 sync contract must lower to a Java
  `@Singleton` `SyncAgent` class during Stage 04e-green. Wired the check into
  Stage 04e and the quality-gate process so missing sync classes fail before
  Stage 05. Profiles whose runtime vocabulary mirrors Stage 03 can opt into
  stricter trigger/fires metadata comparison with `--strict-trigger`.
- **Iterative-change enforcement**: Added
  `quality-gate/verify_iterative_change_readiness.py` and
  `quality-gate/verify_iterative_change_coupling.py` to mechanise R17 before
  and during Stage 04 implementation work. Iterative concept/sync changes now
  require a structured `_changes/` artefact, and implementation changes must
  land with their matching Stage 02/03 artefacts in the same diff.
- **Deterministic guardrails for new contract rules**: Added
  `quality-gate/verify_port_spec_contract.py` to enforce Stage 04b response
  shapes and Stage 04c `@contract` scenarios when Stage 00 produces
  `port-spec.md`. Added `quality-gate/verify_concept_field_assertions.py` to
  enforce R14/R16 for Java concept tests by requiring completion-field
  assertions alongside outcome assertions. Wired both checks into
  `QUALITY_GATE.md` and the Stage 04b/04c/04d templates.
- **Gate summary rule**: Added operating principle 11 to `AGENTS.md §2`
  requiring the agent to list every artefact file produced since the last
  gate, grouped by stage, before presenting the approval question at each
  human gate. Updated Gate sections in all four gate-stage CONTEXT.md files
  (Stage 00, 02b, 03b, 04c) to mandate the summary before approval. The
  human can identify review targets without inspecting the filesystem or
  `git diff`.
- **AGENTS.md §7 capability profiles** now include explicit fences: "No
  implementation code or test files" for Requirements Analysis and Structural
  Modelling groups; "Red phase: tests only. Green phase: implementation only"
  for Implementation group.
- **RULES.md §R9** extended with an outcome branching checklist (6
  verification checks for implementation correctness).
- **AGENTS.md §5** now documents the R1–R5 (WYSIWID architectural) and
  R6–R9 (process/discipline) rule split, with a cross-link to `RULES.md`.
- **`.cursor/rules/clad.mdc`** added R6–R9 pointer to match `AGENTS.md`.

### UC-00-login refresh

- **UC-00-login brought current with updated methodology**: Fixed stale
  gate sections (auto-advance model) in 10 CONTEXT.md files. Added
  `Skill:` entries to Inputs tables. Added missing `_config/build-and-test.md`
  and `_config/package-and-layout.md`. Produced Stage 04d-red and 04e-red
  output/ directories with derivation maps documenting SPEC coverage. Marked
  04d-green and 04e-green as verified (all 46 reference-impl tests pass).
  Produced complete Stage 05 outputs (trace.md with resume point, smoke.md
  with runtime evidence, tracking.md).

### Consistency fixes

- **SYNCHRONIZATIONS.md**: Replaced `freshSessionId()` function call in
  `where` clause example with a Pattern C constant, resolving contradiction
  with `templates/sync.md`'s no-computation-in-where rule.
- **DELIVERY.md**: Commit example changed from per-stage (11) to per-gate (3)
  to match the commit rule in both `DELIVERY.md` and `AGENTS.md`.
- **STAGES.md + 5 CONTEXT.md files**: "Auto-advances to Stage X" changed to
  "Auto-advances (next human gate: Stage X)" — the `→` now correctly means
  the gate destination, not the immediate next stage.
- **STAGES.md**: "the human gates after each" corrected to "the agent gates
  (auto or human) after each" for 04 sub-stages.
- **Gate approval phrasing**: Standardized human-gate CONTEXT.md files (02b,
  03b, 04c) to use the single phrase from `templates/stage-CONTEXT.md`.
- **AGENTS.md §3 table**: Added footnote documenting the "Auto → X"
  convention (X = next human gate, not immediate next stage).
- **Terminology unification**: AGENTS.md R2 changed from "named graph"
  (RDF-specific) to "named persistence region" (storage-agnostic) to match
  `RULES.md`. Applied same fix to `.cursor/rules/clad.mdc`.
- **FLOW_TOKENS.md**: Renamed "three hard rules" to "three constraints" to
  avoid collision with canonical R1-R9.
- **templates/concept.md**: Added missing `zero or more` multiplicity
  annotation; updated flow token template to list all 7 required fields.
- **templates/data-model.md**, **templates/storage.md**: Added methodology
  file references to header comments.
- **STAGES.md 04c outputs**: Aligned to describe Gherkin `.feature` files
  as the sole output format (Native/markdown track removed).
- **Hardcoded Java paths**: Replaced in two CONTEXT.md Verify sections with
  `<APP_TEST_SOURCE_ROOT>` config references.

### Native track cleanup

- **STAGES.md**: Removed all dual-track (Gherkin/Native) language from Gate 3
  table, 04c Process, Output, Gate, and summary table.
- **04_implement/CONTEXT.md**, **03b_data-model/CONTEXT.md**: Removed "or
  native flow-test specs" from gate descriptions.
- **ARTEFACT_MAP.md**: Replaced `<scenario>-flow-test.md` artefact entries
  with Gherkin `.feature` equivalents.
- **WALKTHROUGH.md**, **UC-00-login/README.md**, **UC-00-login 04c
  CONTEXT.md**, **reference-impl/README.md**, **CANONICAL_EXEMPLAR.md**:
  Updated all references from native-track markdown specs to Gherkin
  `.feature` files.
- **Gate restructure**: Reduced per-feature human gates from 15 to 3
  (Requirements at 02b, Architecture at 03b, Executable spec at 04c).
  All other stages auto-advance with quality-gate scripts as the
  mechanised gate between them. Removed the Fast-path section from
  STAGES.md (replaced by auto-advance default). Updated AGENTS.md
  commit rule (accumulate outputs between gates), capability profiles,
  and rejection protocol (defect routes to earliest owning stage within
  a gate block).
- **SPEC format unified**: Concept SPEC files (`04b_spec/output/`)
  changed from code-block format to prose per-action headings with
  explicit `### \`actionName\`` sections, aligning with the UC-00-login
  worked example and making them machine-parseable by the quality-gate
  scripts. Updated `templates/spec.md` accordingly.
- **Project-wide config** (`clad.properties`): Added framework-agnostic
  config file at repo root for `test.framework`, `test.command`, and
  `storage.layer`. Per-feature overrides via `_config/<key>.md`.
  Documented resolution order in AGENTS.md and README.
- **Gherkin/Cucumber BDD track**: Stage
  04c can now mechanically derive executable Gherkin `.feature` files and
  step-definition skeletons from upstream CLAD artefacts (usecase.md,
  chain tables, SPECs, sync specs), replacing hand-written markdown flow
  specs with executable specifications that go green at the end of 04e.
  Includes a comprehensive
  reference at `methodology/architecture/GHERKIN_INTEGRATION.md` with
  structured derivation rules (G1–G5, S1–S3, E1), cross-stage
  consistency checks, and a worked example in the Java reference profile.
  See also `templates/feature.feature` and `templates/step-definitions.java`.
- **Deterministic cross-stage verification scripts**: Expanded the suite
  to 9 profile-agnostic Python scripts under `quality-gate/`. Added:
  `verify_gherkin_derivation.py` (validates `.feature` file derivation
  per GHERKIN_INTEGRATION.md rules G1–G5, S1–S3, E1),
  `verify_concept_test_derivation.py` (validates every SPEC outcome has
  a matching concept test method in Java source). Fixed
  `verify_outcome_alignment.py` to parse comma-separated outcomes in
  chain tables. Fixed `verify_scenario_coverage.py` to handle per-UC
  use cases (slug-based goal matching, double-quoted sync citations,
  conditional chain/sync checks when those artefacts don't exist yet).
  Stage CONTEXT templates updated to invoke the appropriate scripts in
  their `## Verify` sections.
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

### Tooling & CI

- **RDF-star action log migration**: The action log model under
  `reference-impl/java-micronaut-jena/` was migrated from RDF reification
  (`:actions` self-ref, `:output <iri>` + `<iri> :outcome`) to
  RDF-star/SPARQL-star (direct `:outcome` on action nodes, annotation
  syntax `{| |}` for output, blank nodes for input). Eliminates ~2
  triples per action, shortens every sync WHERE clause by one JOIN, and
  removes IRI minting for input/output nodes. SyncAgent now uses
  `parameterizeSparql(String)` instead of `buildSparql()`. SYNC_LOWERING.md
  updated with star pattern examples.

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

- **Dep card column ordering** (UC-02): Normalised dependency review
  cards to match the template's `| Action | Flow (sync) | ...` format
  (was `| Sync | Flow | Action | ...`), fixing `verify_action_chain.py`
  parsing.
- **Chain-table outcome parsing**: Fixed `verify_outcome_alignment.py`
  to handle multiple backtick-quoted outcomes per cell (e.g.
  `` `AVAILABLE`, `UNAVAILABLE` ``) rather than treating the whole cell
  as a single outcome name.
- **Sync citation format**: Fixed `verify_scenario_coverage.py` to
  accept both double-quoted (`"scenario"`) and backtick-quoted
  (`` `scenario` ``) citations in sync specs.
- **Cucumber slash escaping**: Fixed step-definition annotations in
  Gherkin BDD tests to escape `/` in route paths (`POST \/title`)
  which Cucumber Expressions interpret as alternative delimiters.
- **Precondition formatting**: Fixed Gherkin `.feature` Scenario
  Outline examples to use `Given <precondition>` with precondition
  values not prefixed by "And", avoiding invalid Gherkin syntax.
- **Checkstyle baseline**: Updated to 3884 violations (from 2716)
  to accommodate new sync and concept implementations.

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
