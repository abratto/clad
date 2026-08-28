# Changelog

All notable changes to this repository will be documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
from the next published CLAD release onward. Each published CLAD version is
identified by an immutable, annotated Git tag (`vMAJOR.MINOR.PATCH`). This
governance does not prescribe release policy for downstream CLAD-based projects.

Pre-1.0 minor versions can include incompatible methodology changes; the
file `methodology/` is the source of truth for what each version contains.

## [Unreleased]

### Added

#### Deterministic enforcement
- **Artefact gate in test loop**: `verify_artefacts.py` runs before `mvn test` via `clad.properties test.command`. Blocks test feedback when artefacts are broken — no test results without a passing gate. Wired into the self-audit (principle 14), test loop (R19), and pre-commit hook (R18).
- **Anti-bypass hardening**: `--no-verify` banned (R18). Only `CLAD_HOOK_SKIP=1` under explicit human instruction. All documentation and hook output updated.
- **Iterative change gates**: `verify_iterative_change_readiness.py` requires `_changes/` artefacts when stage outputs change. Wired into pre-commit hook and `verify_artefacts.py` test-loop gate. `advance.py` presents git diff review for iterative changes instead of full stage summaries. Receipt freshness check ensures `advance.py` was run for re-entered stages.
- **ActionLog isolation**: `verify_action_log_isolation.py` catches controllers bypassing the engine with raw SPARQL. Catches concept graph literals leaking into infrastructure code. Wired to Stage 04e.
- **Sync declarative enforcement**: `verify_sync_declarative.py` catches imperative branching, `*Coordinator`/`*Orchestrator` classes, and non-final fields in sync implementations. Wired to Stage 04e.
- **Cucumber expression handling**: `verify_step_definition_parity.py` now handles `{string}`, `{int}`, `{float}` parameters, `And`/`But` keywords, and Java source escapes in annotation text. Wired to Stage 04c alongside `verify_step_definition_derivation.py`.

#### Workflow tooling
- **`./clad` CLI wrapper**: Auto-discovers active feature from `RESUME.md`. Subcommands: `advance`, `approve`, `approve-iter`, `verify`, `next`, `stages`, `checklists`, `feature`, `help`. Prefers features with uncommitted `_changes/` files.
- **Task checklists**: `## Progress checklist` section added to all 12 stage `CONTEXT.md` templates. Accessible via `./clad checklists`.
- **Stage renumbering**: `02a_responsibility-map` and `02b_chain-table` renumbered to `01a` and `01b` — they are requirements work alongside Stage 01, not sub-stages of 02 (concepts). 66 files updated.

#### Engine
- **CompletionBus race fix**: `signal()` now uses `getAndUpdate()` for atomic add. `awaitSignal()` guards against stale permits. Fixes intermittent dispatch timeouts under concurrency.
- **RemoteStorage archive fix**: `archiveFlow()` now INSERTs into archive graph then DELETEs from action graph (matching `LocalStorage`), instead of permanently deleting flow triples.

#### Deployment
- **Docker Compose stack**: `docker-compose.yml` + `Dockerfile` deploy the full CLAD stack (app + Fuseki TDB2 + Ollama LLM) as `docker compose up`. Fuseki config with pre-created `/clad` dataset. Tested end-to-end with login API, Fuseki health check, and Ollama serving.

#### Analysis
- **Axiomatic analysis**: Three new Stage 03 checks — `verify_sync_cycle_graph.py` (A→B→A cross-concept cycles), `verify_sync_overlap.py` (deadlock risk from overlapping sync lock orders), `verify_concept_matrix.py` (FR×DP matrix with God Object, duplication, and entanglement detection). All accept `--advisory` for refactoring analysis on existing projects. Field-tested against Conduit (7 features, 40+ syncs) and legalmatcherpoc (13 features, 67 syncs).

#### Documentation
- **ARCHITECTURE MAP rewrite**: ARTEFACT_MAP.md rewritten with two-column approach. Three-phase formal sync semantics added to SYNCHRONIZATIONS.md.
- **Concept definition heuristics**: `CONCEPTS.md` §"Is it a concept?" — 7 tests with a 4-gate decision flowchart for agents at Stage 01a.
- **Frames model**: SYNCHRONIZATIONS.md now explains how syncs fan out — one invocation per SPARQL result row.
- **TRACEABILITY.md**: Complete artefact-to-architecture-to-code mapping table plus enforcement script reference. Linked from AGENTS.md, methodology/README.md, ARTEFACT_MAP.md.
- **Modular monolith section**: Documents WYSIWID as code-level (not network-level) boundaries, with tradeoff discussion for distributed systems.
- **Docker Compose deployment** docs in reference-impl README.
- **Session transcript** from WALKTHROUGH.md added to README.
- **Conduit project** linked from README as "Built with CLAD" example.
- **README restructuring**: 60% reduction, clearer narrative arc.
- **Guarantees section**: Four core CLAD guarantees in README.
- **Skill fallback table**: AGENTS.md §4b — agents without Skill support get raw file paths.
- **Tastetag references**: Private repo links removed from CITATIONS.md and ENGINE.md.

### Changed
- **Stage renumbering**: `02a`→`01a`, `02b`→`01b` (66 files).
- **Sync patterns collapsed**: A/B/C/D → "internal flow data" vs. "concept-state read" (10 files).
- **ArchUnit branching check widened**: Now scans all `infrastructure/**/*.java`, not just `*Web*`.

### Fixed
- CompletionBus race condition dropping dispatch signals.
- RemoteStorage archive semantics (delete → archive).
- Config parser: `_read_config` used `configparser` on INI-free `clad.properties`.
- `cucumber_green` check moved from Stage 04c to 04e (deadlock — tests can't be green until implementation).
- `verify_cucumber_green.py` cwd fixed to use repo root.
- Principles 2 and 12 contradiction resolved — stage transitions delegated to `advance.py`.
- `verify_iterative_change_readiness.py` scoped diff to feature (was global).
- Field value parser now handles backtick-enclosed values.
- `./clad` now uses `$PWD` for feature discovery (was `SCRIPT_DIR`).
- Active feature prefers uncommitted `_changes/`, ignores committed artefacts from earlier work.

### Release governance

- **Annotated release tags**: Documented SemVer compatibility expectations and
  made an annotated `vMAJOR.MINOR.PATCH` tag on a green `main` commit the
  authoritative release boundary. Agents prepare release evidence but require
  explicit human authorization to create or publish a release.

### Reference profile

- **Remote Fuseki hardening**: Remote storage now fails closed for invalid
  backend configuration, uses a five-second connection timeout, bounds Basic
  authentication to one challenge retry, keeps remote archival request-atomic,
  and requires an explicit Compose administrator password.
- **Quality-gate parser correctness**: Implementation-parity and
  sync-implementation-parity checks now parse current Sync Contract Matrix
  notation, while Cucumber verification counts JUnit Platform scenarios
  correctly. Focused parser-regression fixtures cover the accepted and
  malformed forms.

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
## [0.2.0] — 2026-08-28

### Added

#### Engine — fire-after-commit

- **`legible-engine`** — a zero-dependency engine (`dev.legible.engine`) that
  realises the Meng & Jackson synchronization semantics directly. Concepts hold
  state as relations behind a `FactStore`/`Region` SPI; actions are map→map;
  syncs are declarative `when`/`where`/`then` rules (`SyncRule`) evaluated by a
  `WhereEvaluator` (fan-out, Pattern D reads, `OPTIONAL`, `bind(uuid)`,
  `?_eachthen` grouping, route `Guard`s). Coordination happens **after** an
  action is committed to a per-flow action log — there are no transactions and
  no rollback; a failing downstream action completes with a named `error`
  outcome. The action log carries `parentActionId`/`causedBySync` provenance
  edges.
- **`java-legible`** — the canonical in-memory profile: UC-00-login plus
  example features (social, tagging, token) exercising the full sync model, and
  a flow-token back-trace (`FlowTraceTest`) that asserts the runtime chain
  matches the chain table.

#### Engine — storage

- **`legible-storage`** — `JenaFactStore` (one named graph per concept) and
  `PostgresFactStore` (a generic `fact` relation) prove the engine is
  storage-agnostic: the same `Concept`/`SyncRule` code runs on in-memory, Jena,
  and Postgres with identical outcomes.
- **`RmapPostgresFactStore`** — relation realization: Halpin's Rmap derives one
  typed table per concept (individual identifier as primary key, one
  `TEXT`/`INTEGER`/`TIMESTAMP` column per fact type, `DEFAULT` for resettable
  facts, `UNIQUE` from the model). String↔typed values round-trip through the
  SPI; mandatory roles are schema metadata (not `NOT NULL`) because the
  per-fact SPI cannot satisfy row-level mandatory atomicity.

### Changed

- **UC-00-login re-lowered** — the bootstrap entry action is reconciled to the
  paper's `Web/request` (collapsing the old "bootstrap handoff exception"), the
  `refused` outcome is reconciled across chain tables and SPECs, and the
  concepts/syncs are re-implemented as `Concept`/`SyncRule`.
- **Flow tokens** now materialise as a per-flow `ActionLog` of
  invocation/completion records with explicit provenance (was a bare UUID IRI
  in an RDF graph).
- **Methodology and rules** — `ENGINE.md` rewritten; `TRACEABILITY.md`,
  `ARTEFACT_MAP.md`, `SYNCHRONIZATIONS.md`, `CONCEPTS.md`, `WEB_CONCEPT.md`,
  `FLOW_TOKENS.md`, `SYNC_PATTERNS.md`, `STORAGE_MAPPING.md` updated. `AGENTS.md`
  retires R10 (reserved SPARQL variables) and R21 (RDF-star programmatic APIs),
  and rewords R11/R12/R16 to the declarative engine. Concept-naming and
  relational-state guidance carried into the engine's `Concept`/`Region`
  javadoc.
- **Parity scripts** now understand the `SyncRule`/`Concept` shape (and remain
  backward-compatible with the legacy `SyncAgent`/`ConceptAgent`);
  `verify_sync_declarative.py` skips concept classes.

### Why

The previous engine encoded the "sync-as-transaction" reading of *The Essence
of Software* (an atomic composite write with rollback). Jackson's forum reply
and Meng's papers (`arXiv:2508.14511`, `arXiv:2606.11051`) show the DSL "gets
rid of the need for transactions". The fire-after-commit engine follows that
model: the action is the atomic unit, failures are named outcomes, and the log
is the source of truth. Benefits: no 2PC/saga machinery, storage-agnostic
(`FactStore` SPI), ~100× lower latency / ~50× throughput, per-flow log sharding
plus per-concept serialisation, and richer provenance for Stage 05.

## [0.1.10] — 2026-08-26

### Fixed

#### Quality gate

- **Narrow the relational-state check.** `verify_concept_state_relational.py` now flags only *untyped* field names (`userid`, `username`, `password`) as the object-oriented trap, not every field lacking a `->` arrow. Typed collection/relation forms (`leadLog: List<LeadRecord>`, `attorneyStatus: Map<AttorneyId, Availability>`, `clientId: String -> { … }`) are legitimate relational state. Also skips (rather than fails) a feature whose concept dir has no `.concept.md` files (concept reuse via `_REUSES_*.md`).

## [0.1.9] — 2026-08-14

### Changed

#### Quality gate

- **Relational concept state enforced at Stage 02.** New `verify_concept_state_relational.py` check fails a concept spec whose state block lists bare instance variables (`userid, username, password`) instead of relations over a set of individuals (`username: UserId -> String`), or whose field subject type is the concept's own name. Implements Daniel Jackson's *Why concepts aren't objects* as a deterministic gate. `CONCEPTS.md` gains heuristic #8 and views-separation guidance; `templates/concept.md` updated to match.

## [0.1.8] — 2026-08-14

### Changed

#### Quality gate

- **Gate approval is bound to artefact content.** `approve_gate.py` records a content hash over the gate's stage outputs beside each approval. `verify_stage_sequence.py` and `verify_gate_approval.py` treat a human-`approved` gate as stale when the hash is missing or no longer matches, forcing the gate to be re-presented. `auto-approved` gates remain exempt (documented escape hatch). Closes the "inherited approval" hole where an agent re-entering a feature could re-derive a gate's stages and advance without re-review. `--baseline` migrates pre-existing approvals.

## [0.1.7] — 2026-08-13

### Changed

#### Reference profile — Java/Micronaut/Jena

- **Single transactional engine.** The reference (non-transactional) engine is removed; the transactional engine is now the only engine. `ConceptAgent` performs pre-commit sync evaluation and atomic composite writes. `SyncEvaluator` (renamed `PredicateSyncDispatcher`) is the sync-matching index. The `engine.mode` property and the `engine/predicate/` package are removed.

## [0.1.6] — 2026-08-13

### Changed

#### Reference profile — Java/Micronaut/Jena

- **Action log is always in-memory.** `SplitStorage` is now the default backend for every profile: the action log (transient, high-churn execution state) always lives in in-memory Jena (`TxnMem`); only durable business graphs use the backend selected by `engine.dataset.type`.
- **Archive graph removed, replaced by a log sink.** The `engine.archive.flows` toggle and the `ACTION_ARCHIVE_GRAPH_IRI` graph are gone. Completed flows are now flushed to a pluggable `FlowArchiveSink` (`logger` default, `devnull` to discard) before deletion, controlled by `engine.archive.sink`. `S3Sink` is deferred pending an AWS SDK dependency decision.

### Fixed

- **Concurrency correctness under load.** Serialized the dispatch quiescence iteration with a fair lock, closing a read-then-write race in `findPendingInvocations` that produced duplicate `respond` actions and cross-flow field contamination under concurrency. `ConcurrencyTest` now passes at 1–32 threads with zero errors (previously 1103 errors at 8 threads).
- **Debug endpoint rehydration.** `GET /api/dev/flow/{token}` now reports `actionCount`/`actions` after the archive-buffer fallback, and the archiver and debug endpoint share the same `FlowArchiveBuffer` singleton.

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
