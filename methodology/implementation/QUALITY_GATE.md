# Quality gate — pre-commit checks

A **quality gate** is the small set of checks every commit on a CLAD
project must pass before being pushed. This file describes the
language-agnostic gate, then the gate as it applies to the
Java/Micronaut/Jena profile that ships with this starter.

The gate is intentionally small. A long gate that nobody runs is
worse than a short gate that everybody runs.

## How quality gates relate to stage gates

CLAD's per-feature workflow uses **3 human gates** (Requirements, Architecture,
Executable spec) with auto-advance between them. Between every auto-advance step,
the agent runs the relevant quality-gate scripts from this table. If any script
fails, the agent stops and surfaces the defect — it does not silently advance.

The quality-gate scripts are therefore the **mechanised gate** for auto-advance
stages. A script that passes gives the agent confidence to proceed; a script that
fails sends work back to the owning stage just as a human rejection would.

---

## Language-agnostic principles

These hold for every profile. Adapt the *commands* per profile; do
not relax the *intent*.

1. **Format clean.** Code is formatted by the profile's standard
   formatter; running the formatter changes nothing.
2. **Lint clean.** The profile's standard linter reports zero issues
   on the files in the diff. (Whole-tree lint cleanliness is a
   separate goal.)
3. **No `TODO`/`FIXME` without a tracked issue.** A `TODO` is fine if
   it cites a tracker entry (`TODO(#123): ...`); naked `TODO`s do not
   pass.
4. **Tests green.** All tests touched by the diff, plus the full
   flow-test suite for any feature whose stage 04c artefacts changed,
   pass locally.
5. **Hard-rule check passes.** Whatever mechanism the profile uses to
   enforce R1/R2/R4 (architecture tests, lint plugin, custom script)
   runs and is green. R1 is the easiest to break by accident; the
   gate is what catches it.
6. **Stage outputs not edited out-of-band.** If the diff modifies a
   `stages/NN_*/output/` file, the diff also reflects an
   `Owner stage = NN` so a reviewer can see which stage produced the
   change. Edits to a stage's output that did not come from re-running
   that stage are flagged.
7. **Stage 01 use-case consistency checks (automated + semantic).**
   When a diff touches
   `features/UC-*/stages/01_usecase/output/usecase.md`:
   - **Automated:** Run `quality-gate/verify_scenario_coverage.py`
     to check every in-scope goal has a scenario, every scenario has
     a chain file, and every scenario is cited by a sync.
   - **Automated:** Run `quality-gate/verify_file_manifest.py`
     to check `output/` contains exactly the expected files.
   - **Semantic (human):** Verify every scenario's main flow starts
     with an action by an actor, no domain entity is named as an
     actor, and every scenario has an explicit trigger statement.
8. **Stage 02 outcome alignment and chain-table checks.**
   When a diff touches `features/UC-*/stages/02_concepts/` or
   `features/UC-*/stages/02b_chain-table/`:
   - **Automated:** Run `quality-gate/verify_outcome_alignment.py`
     to check every chain-table outcome matches a SPEC outcome enum.
   - **Automated:** Run `quality-gate/verify_action_chain.py`
     to check action names flow consistently from responsibility map
     through chain tables, concept specs, syncs, cards, and SPECs.
   - **Automated:** Run `quality-gate/verify_file_manifest.py`
     for each stage's `output/` directory.
   - **Semantic (human):** Verify no bootstrap concept file
     (`Web.concept.md`, etc.) appears in `02_concepts/output/`
     without an explicit deviation. Verify concept boundaries are
     coherent.
9. **Stage 03 sync contract checks (automated + semantic).**
   When a diff touches `features/UC-*/stages/03_syncs/`:
   - **Automated:** Run `quality-gate/verify_sync_matrix.py`
     to verify every sync has a complete Sync Contract Matrix.
   - **Automated:** Run `quality-gate/verify_sync_route_filters.py`
     to detect shared-trigger syncs that are missing route filters.
   - **Automated:** Run `quality-gate/verify_file_manifest.py`
     to check output files match the expected list exactly.
   - **Automated:** Run `quality-gate/verify_scenario_coverage.py`
     to check every scenario is cited by at least one sync.
   - **Semantic (human):** Verify no response payload invents fields
     not present as approved constants or emitted action-outcome
     fields. Verify no imperative branching over business state.
10. **Stage 03b data model checks (automated + semantic).**
    When a diff touches `features/UC-*/stages/03b_data-model/`:
    - **Automated:** Run `quality-gate/verify_data_model.py`
      to check all 7 CSDP steps are present, all sub-sections exist,
      constraint sections have content or "None", no storage-leakage
      patterns, and no cross-concept entity type references.
    - **Automated:** Run `quality-gate/verify_file_manifest.py`
      to check one data model file per concept.
    - **Semantic (human):** Verify elementary facts are correctly
      identified and entity-type combination decisions are sound.
11. **Stage 04 implementation-stage checks (automated).**
     When a diff touches `features/UC-*/stages/04_implement/`:
     - **Automated:** Run `quality-gate/verify_feature_file_presence.py`
       as a pre-flight before any 04c work.
     - **Automated:** Run `quality-gate/verify_spec_parity.py`
       to check every concept spec action has a matching SPEC entry.
     - **Automated:** Run `quality-gate/verify_port_spec_contract.py`
       when `port-spec.md` exists to check Stage 04b response shapes and
       Stage 04c `@contract` scenarios are present.
     - **Automated:** For the Gherkin track, run
       `quality-gate/verify_gherkin_derivation.py` to validate derivation.
     - **Automated:** Run `quality-gate/verify_concept_test_derivation.py`
       to check every SPEC outcome has a matching concept test.
     - **Automated:** For Java concept tests, run
       `quality-gate/verify_concept_field_assertions.py` to confirm tests
       assert required completion field values, not only outcome tokens.
     - **Automated:** At the end of Stage 04e-green, run
       `quality-gate/verify_sync_implementation_parity.py` to confirm every
       approved Stage 03 sync contract has a matching Java `SyncAgent`
       implementation class.
     - The automated checks replace the previous semantic (human) checks.
       04d and 04e auto-advance; the scripts are the gate.
12. **Implementation parity checks (R17 enforcement).**
    When a diff touches any implementation source file under a profile's
    sync or concept packages (e.g. `app/backend/src/.../syncs/`,
    `app/backend/src/.../concepts/`, or the equivalent in
    `reference-impl/`):
    - **Automated:** Run `quality-gate/verify_iterative_change_readiness.py`
      with `--feature features/UC-XX-<slug>`. The check fails when an
      iterative concept/sync spec or implementation change lacks a structured
      `_changes/` artefact with change category, earliest re-entry stage,
      artefact-impact matrix, and re-derivation order.
    - **Automated:** Run `quality-gate/verify_iterative_change_coupling.py`.
      The check fails if a concept/sync implementation file changed without
      its corresponding Stage 02 concept spec or Stage 03 sync spec changing
      in the same diff.
    - **Automated:** Run `quality-gate/verify_implementation_parity.py`
      with `--sync-impl-dir` and/or `--concept-impl-dir` pointing at the
      changed packages, and `--features-dir features/`. The check fails
      if any implementation class lacks a corresponding spec artefact,
      or if any sync spec/class/runtime name does not mechanically follow
      the `When<Trigger>Then<Target>[For<Scope>]` naming grammar derived
      from the Stage 03 sync rule.
    - **Automated:** Run `quality-gate/verify_sync_implementation_parity.py`
      with `--sync-impl-dir` pointing at the changed sync package and either
      `--sync-dir` for the active feature or `--features-dir features/` for a
      whole-tree gate. The check fails if any Stage 03 sync contract lacks a
      matching `@Singleton` `SyncAgent` implementation. Profiles whose runtime
      vocabulary mirrors Stage 03 exactly may add `--strict-trigger` to also
      require trigger/fires metadata to match the contract's `when`/`then`
      signatures.
    - **Semantic (human):** Verify the diff also contains updates to the
      relevant `stages/02_concepts/output/` or `stages/03_syncs/output/`
      artefacts. A Java-only diff with no artefact update is a hard-rule
      (R17) violation even if the parity script passes (e.g. the spec
      file exists but its content no longer matches the code).

## Java/Micronaut/Jena profile

The reference profile under `reference-impl/java-micronaut-jena/`
maps the principles above to:

| Principle | Command |
|---|---|
| Format clean | `mvn spotless:apply` (then `spotless:check` is part of `verify`) |
| Lint clean | bundled into `mvn verify` |
| Tests green | `mvn verify` runs unit + integration |
| Hard-rule check | `LegibleArchitectureRulesTest` (ArchUnit) runs as part of `mvn verify` |
| Smoke check (when relevant) | `mvn exec:java` then exercise the route per Stage 05 closure |

The single command that exercises the gate is:

```
mvn verify
```

If `mvn verify` is green and the diff has no naked `TODO`/`FIXME`,
the commit is gate-clean. Pre-push hooks may automate the check; the
hook is convenience, not the gate itself.

### Quality-gate scripts (profile-agnostic)

The repo ships a set of profile-agnostic verification scripts under
[`quality-gate/`](../../quality-gate/) that automate cross-stage
consistency checks across the CLAD artefact chain:

| Script | Stage(s) | What it checks |
|---|---|---|
| `verify_stage_sequence.py` | Any | No stage was skipped (contiguous prefix), and each cleared human gate is recorded as approved in `RESUME.md` |
| `verify_file_manifest.py` | Any | `output/` contains exactly the expected files |
| `verify_scenario_coverage.py` | 01, 02b, 03 | Goal → scenario → chain → sync coverage |
| `verify_outcome_alignment.py` | 02 | Chain-table outcomes match SPEC enums |
| `verify_action_chain.py` | 02–04b | Action names consistent across all artefacts |
| `verify_sync_matrix.py` | 03 | Every sync has a complete Sync Contract Matrix |
| `verify_sync_route_filters.py` | 03, 03a | Shared-trigger syncs carry route filters |
| `verify_data_model.py` | 03b | CSDP structure, storage-leakage prevention |
| `verify_spec_parity.py` | 04b | Action name parity between concept specs and SPECs |
| `verify_port_spec_contract.py` | 04b, 04c | When `port-spec.md` exists, response shapes and `@contract` scenarios are present |
| `verify_iterative_change_readiness.py` | 04+ | Iterative concept/sync spec or implementation changes have a structured `_changes/` classification and artefact-impact matrix |
| `verify_iterative_change_coupling.py` | 04+ | Concept/sync implementation changes are committed with their matching Stage 02/03 artefacts |
| `verify_implementation_parity.py` | 04+ | Implementation concept/sync classes have corresponding stage artefact specs; sync names lower mechanically from Stage 03 rules |
| `verify_sync_implementation_parity.py` | 04e | Stage 03 sync contracts have corresponding Java `SyncAgent` implementations |
| `verify_feature_file_presence.py` | 04c | Pre-flight: `.feature` file exists in output + Cucumber discovery path |
| `verify_gherkin_derivation.py` | 04c | `.feature` file derivation per GHERKIN_INTEGRATION.md rules G1–G5, S1–S3, E1 |
| `verify_concept_test_derivation.py` | 04d | Every SPEC outcome has a matching concept test row and Java method |
| `verify_concept_field_assertions.py` | 04d | Java concept tests assert required completion fields from SPEC flow-token shapes |
| `verify_step_definition_parity.py` | 04c | Every Gherkin step has a matching step-definition method with a non-empty body — catches empty stubs |
| `verify_step_definition_derivation.py` | 04c | Every chain-table business action name appears in at least one step-definition method body — catches methods that don't exercise the chain-table actions they were derived from |
| `verify_cucumber_green.py` | 04e-green | Runs the test command and confirms all Cucumber scenarios pass (fails on undefined, pending, skipped, or failing scenarios) |

Each script returns exit code 0 on pass, 1 on fail, with a structured
report. Profile-agnostic scripts are invoked by `advance.py` via
`clad_stages.py`; profile-specific scripts (including the Cucumber and
step-definition checks) are invoked from the relevant stage's `## Verify`
section.

### Installing the local pre-commit hook (opt-in, strongly recommended)

The scripts above run deterministically **when invoked**, but nothing
forces the agent (or you) to invoke them before a commit. CLAD ships an
opt-in git hook that closes that gap: it runs the sequence guard and the
iterative-change coupling check automatically on every `git commit`, and
**refuses commits that skip a stage or decouple an implementation from
its spec**.

Git never runs hooks from a fresh clone (the `.git/hooks/` directory is
not version-controlled), so CLAD stores the hook under the tracked
[`.githooks/`](../../.githooks/) directory and activates it with a
one-time installer:

```bash
./quality-gate/install-hooks.sh
```

This runs `git config core.hooksPath .githooks` for your clone. After
that, `git commit` runs [`.githooks/pre-commit`](../../.githooks/pre-commit),
which:

1. Reads the staged diff and finds every touched per-UC feature root
   (`features/UC-*/`).
2. Runs `verify_stage_sequence.py` for each of those features and
   `verify_iterative_change_coupling.py` once.
3. If any check fails, prints a `COMMIT BLOCKED` banner naming the
   skipped stage (and where its artefacts belong) or the decoupled
   change, and aborts the commit.

Environment toggles:

| Variable | Effect |
|---|---|
| `CLAD_HOOK_SKIP=1` | Skip the hook for this invocation |
| `CLAD_HOOK_REQUIRE_RECEIPTS=1` | Also require a current gate receipt per populated stage (`--require-receipts`) |

Bypass a single commit with `git commit --no-verify`; uninstall with
`git config --unset core.hooksPath`.

**Cloning CLAD as a template?** Run `./quality-gate/install-hooks.sh`
once right after cloning. The hook is optional so CLAD stays usable
without it, but it is the cheapest way to keep the stage pipeline honest
— it turns "the agent should have run the sequence guard" into "the
commit cannot land until the pipeline is intact."

### What the ArchUnit rules enforce

`LegibleArchitectureRulesTest` codifies R1–R5 for the Java profile:

- **R1:** No class under `com.example.app.concepts.<X>` may import a
  class under `com.example.app.concepts.<Y>` for any other concept `Y`.
- **R2 (heuristic):** One `*Concept` class per concept package.
- **R3:** Sync classes are `SyncAgent` subclasses with only final
  fields. No imperative branching in sync source. No
  `*Coordinator`/`*Orchestrator` classes without explicit waiver.
- **R4:** Only `infrastructure.WebController` has HTTP annotations.
  Web boundary does not depend on business concepts directly. No
  imperative branching in Web boundary code without a transport waiver.
- **R5 (heuristic):** Every `*Concept` class extends `ConceptAgent`,
  ensuring participation in the action-log polling loop.

If you add new rules (e.g. R2 enforcement when an RDF profile is
wired), extend that test class. The test class is the codified form
of the rules in [`RULES.md`](RULES.md).

## Other profiles

A profile under `reference-impl/<other>/` that wants to claim CLAD
compliance must publish, in its `README.md`:

- The single command that runs the gate.
- The mechanism enforcing R1, R2, R4 (with a pointer to the file or
  test).
- Anything specific to that language's idioms (e.g. `mypy --strict`
  for Python, `tsc --noEmit` for TypeScript).

The expectation is that **one command** runs the whole gate. If a
profile needs five commands chained, it is not yet ready.
