# Stage 04c — Flow tests (outer red)

## Why this stage exists

The **outer red** of the outside-in TDD double-loop. One failing flow
test per use-case scenario, each asserting (a) the HTTP request, (b)
the expected sequence of flow tokens, and (c) the response. These tests
stay red through 04d (concept TDD) and go **green at the end of 04e**
(sync TDD). They are the executable form of the use case — if they
pass, the scenario passes; if they don't exist, the scenario isn't
covered.

Flow tests use **Cucumber/BDD (Gherkin)**, the recommended outer-red track.
The `.feature` file IS the spec — a Gherkin Scenario maps 1:1 to a
use-case scenario, with no invented steps.

**Feeds:**

- `<feature>.feature` → 04e (Cucumber scenarios go green at the end);
  05 (Gherkin scenario names link the trace to executable specs).
- `<Feature>StepDefinitions.java` (skeleton, `@Disabled`) → the outer
  loop of TDD itself.
- `../../../../templates/feature.feature` → Gherkin output template
  with derivation rules.

**Agent stance for this stage:** these tests must read like the use
case. If they read like a unit test, you are testing the wrong layer.
Read `methodology/implementation/TDD.md` before writing anything.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../01_usecase/output/usecase.md` | 4 | Scenarios to test |
| `../../02b_chain-table/output/` | 4 | Action chain per scenario — step-definition derivation |
| `../../03_syncs/output/` | 4 | Expected coordination |
| `../04b_spec/output/` | 4 | Action signatures and outcome values |
| `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md` | 4 | Required when present; external adapter contract for `@contract` scenarios |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command for compilation evidence |
| `../../../_config/package-and-layout.md` | 3 | Canonical test-source root and package layout |
| Skill: `clad-flow-testing` | 3 | Flow testing reference (see skills/ directory) |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics, casing rules, payload rules |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School double-loop discipline |
| `../../../../../templates/feature.feature` | 3 | Gherkin output template with derivation rules |
| `../../../../../templates/step-definitions.java` | 3 | Step-def skeleton template |

## Process

1. **Derive** a Gherkin `.feature` file from `../../01_usecase/output/usecase.md`
   using the derivation rules in `../../../../../templates/feature.feature`:
   one `Feature` per use case, one `Scenario` (or `Scenario Outline`) per
   named scenario, one `Given`/`When`/`Then` step per precondition/trigger/
   postcondition.
2. **Derive** a step-definition class skeleton from
   `../../02b_chain-table/output/` (action chain per scenario) and
   `../04b_spec/output/` (action signatures, outcome enums) using the
   template at `../../../../../templates/step-definitions.java`.
   One method per chain-table row. `@Disabled` the skeleton so the tests
   start red.
3. Ensure a Cucumber JUnit runner class (e.g. `CucumberTest.java`) exists
   under `APP_TEST_SOURCE_ROOT`, packaged under `APP_PACKAGE_ROOT`, pointing
   at the `.feature` file's resource directory.
4. Place the `.feature` file under
   `APP_TEST_SOURCE_ROOT/resources/features/<feature-name>.feature`.
   Place step-definition classes under `APP_PACKAGE_ROOT.steps`.
5. Before claiming "red and ready", run the canonical build-and-test
   command from `../../../_config/build-and-test.md` (or the targeted
   equivalent documented there) and verify test compilation succeeds. At
   this stage, acceptable red evidence is either
   disabled/skipped tests (when stubs are intentionally `@Disabled`)
   or failing tests if enabled; compilation errors are not
   acceptable.
6. If `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md`
  exists, add at least one `@contract` scenario per HTTP endpoint. These
  scenarios assert exact JSON paths, field types constrained by the
  external contract, and the primary failure path's exact error envelope
  shape. Keep these distinct from `@happy-path` and `@failure-path`
  intent scenarios.

**Token chain rules (read `FLOW_TOKENS.md` in full before writing):**
- Outcome values MUST be SCREAMING_SNAKE_CASE, copied from the SPEC slice.
- Token count = number of rows in the chain table — no phantom intermediate tokens.
- Passwords and secrets MUST NOT appear in any token payload.

## Outputs

- `output/<feature-name>.feature` — one feature file per use case
- (Side effect:) `CucumberTest.java` (runner) + `<Feature>StepDefinitions.java` (skeleton, `@Disabled`)

## Verify

### Pre-flight: feature file presence

Run this **before** any other 04c work. It ensures a `.feature` file
exists for the feature:

```
python3 ../../../../../quality-gate/verify_feature_file_presence.py \
  --feature-output-dir output \
  --feature-files-dir <APP_TEST_SOURCE_ROOT>/resources/features/
```

- **verify_feature_file_presence.py:** asserts that a `.feature` file
  exists in `output/` and in the Cucumber discovery path.

### Automated checks

```
python3 ../../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<feature-name>.feature,…"  # one .feature file per use case
python3 ../../../../../quality-gate/verify_gherkin_derivation.py \
  --usecase ../../01_usecase/output/usecase.md \
  --feature <relevant>.feature \
  --sync-dir ../../03_syncs/output
python3 ../../../../../quality-gate/verify_step_definition_parity.py \
  --feature-files-dir <APP_TEST_SOURCE_ROOT>/resources/features/ \
  --glue-dir <APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT_PATH>/steps/
python3 ../../../../../quality-gate/verify_step_definition_derivation.py \
  --chain-dir ../../02b_chain-table/output \
  --glue-dir <APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT_PATH>/steps/
python3 ../../../../../quality-gate/verify_port_spec_contract.py \
  --port-spec ../../../../../features/_system/stages/00_actor-goal/output/port-spec.md \
  --spec-dir ../04b_spec/output \
  --feature-dir output
```

- **verify_file_manifest.py:** `output/` contains exactly the expected
  `.feature` file(s).
- **verify_gherkin_derivation.py:** every use-case scenario has a
  matching Gherkin Scenario, every Scenario has Given/When/Then,
  response status codes match sync spec `then` clauses (per
  GHERKIN_INTEGRATION.md rules G1–G5, S1–S3, E1).
- **verify_port_spec_contract.py:** skips when no `port-spec.md` exists;
  otherwise checks response-shape SPEC output and `@contract` scenarios
  are present.

### Semantic checks

- Every named scenario in `usecase.md` has a corresponding Gherkin
  `Scenario` (happy path) or `Scenario Outline` (failure branches).
- When `port-spec.md` exists, every HTTP endpoint has at least one
  `@contract` scenario.
- Every `@contract` scenario asserts exact JSON paths and constrained
  field types; it does not use string-contains as a substitute for shape
  checks.
- Every `@contract` scenario asserts the exact error envelope shape for
  the primary failure path.
- Every Gherkin `Given` step traces back to a use-case precondition.
- Every Gherkin `When` step traces back to a use-case main-flow step 1.
- Every Gherkin `Then` step traces back to an expected outcome or
  postcondition — no invented assertions.
- Every step-definition method maps to a chain-table row (by matching
  the action name in its body).
- Outcome values in step-definition assertions are SCREAMING_SNAKE_CASE,
  copied from `04b_spec/output/`.
- Step-definition classes are `@Disabled` or the Cucumber runner is
  configured to skip them.
- The `.feature` file parses without syntax errors (validate with
  `cucumber --dry-run` or the profile equivalent).
- Executed build-and-test command shows test compilation succeeds.
- No Gherkin `Scenario` or step exists without a corresponding
  use-case element.

### Cross-stage checks

- An executed build-and-test command proves test compilation succeeds;
  no compile errors.
- All outcome values are SCREAMING_SNAKE_CASE.
- No passwords or secrets appear in any token payload.
- Token count per scenario equals the number of rows in the
  corresponding chain table.
- **Cross-stage check (back):** the expected token chain matches the
  syncs in `03_syncs/output/` (no surprise tokens).
- **Cross-stage check (forward):** the expected authored action chain is
  concrete enough that `04e` can prove the scenario went green through
  authorised concept actions and syncs, not by response-only shortcuts.
- **Completion rule:** `04c` is not complete from spec artefacts alone.
  The stub test files and the executed compilation evidence are part of
  the stage contract.

## Gate instruction — STOP AND PRESENT

### Step 1 — Present artefacts

Run:

```
python3 ../../../../../quality-gate/present_gate.py \
  --feature ../../../ \
  --gate 3
```

Present the output to the human. **Do NOT proceed past this point.**

### Step 2 — Wait for human approval

Wait for the human to say "approved" (or "Gate 3 approved").
Do NOT update RESUME.md yourself.

### Step 3 — Record approval

Only after the human explicitly approves, run:

```
python3 ../../../../../quality-gate/approve_gate.py \
  --feature ../../../ \
  --gate 3
```

This updates RESUME.md to mark Gate 3 as approved.

### Step 4 — Proceed

After `approve_gate.py` exits successfully, proceed through stages
04d, 04e, and 05 (auto-advance, no further human gates).

The `verify_file_manifest.py` and `verify_gherkin_derivation.py` scripts
must pass before requesting the gate.

## Next stage

→ [`../04d_concept-tdd/CONTEXT.md`](../04d_concept-tdd/CONTEXT.md) — Inner red→green per concept

To advance, the human says: **"Proceed to Stage 04d."**
