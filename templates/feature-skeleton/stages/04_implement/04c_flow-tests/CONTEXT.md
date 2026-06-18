# Stage 04c — Flow tests (outer red)

## Why this stage exists

The **outer red** of the outside-in TDD double-loop. One failing flow
test per use-case scenario, each asserting (a) the HTTP request, (b)
the expected sequence of flow tokens, and (c) the response. These tests
stay red through 04d (concept TDD) and go **green at the end of 04e**
(sync TDD). They are the executable form of the use case — if they
pass, the scenario passes; if they don't exist, the scenario isn't
covered.

**Two tracks are available, selected by the profile's test framework:**

| Track | Profile requirement | 04c outer-red artefact |
|---|---|---|
| **Gherkin** | Cucumber/Gherkin support (Java, Ruby, JS, .NET, Python, Go — Cucumber-ecosystem profiles) | `<feature>.feature` (Gherkin) + `<Feature>StepDefinitions.java` skeleton |
| **Native** | No Cucumber support, or profile opts out of Gherkin | `<scenario>-flow-test.md` (markdown) + `<Scenario>FlowTest.java` stub |

Both tracks produce the same verification surface in Stage 05. The
choice is a profile capability, not a methodology difference. The
track is declared in `../../../_config/test-framework.md` by setting
`TEST_FRAMEWORK=CUCUMBER` or `TEST_FRAMEWORK=NATIVE`. Default to the
Gherkin track when the profile supports Cucumber; fall back to native
otherwise.

**Feeds (Gherkin track):**

- `<feature>.feature` → 04e (Cucumber scenarios go green at the end);
  05 (Gherkin scenario names link the trace to executable specs).
- `<Feature>StepDefinitions.java` (skeleton, `@Disabled`) → the outer
  loop of TDD itself.
- `../../../../templates/feature.feature` → Gherkin output template
  with derivation rules.

**Feeds (native track):**

- `<scenario>-flow-test.md` → 04e; 05.
- `<Scenario>FlowTest.java` (`@Disabled`) → outer loop of TDD.

**Agent stance for this stage:** these tests must read like the use
case. If they read like a unit test, you are testing the wrong layer.
Read `methodology/implementation/TDD.md` before writing anything. On
the Gherkin track, the `.feature` file IS the spec — a Gherkin Scenario
should map 1:1 to a use-case scenario, with no invented steps.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../01_usecase/output/usecase.md` | 4 | Scenarios to test |
| `../../02b_chain-table/output/` | 4 | Action chain per scenario — step-definition derivation |
| `../../03_syncs/output/` | 4 | Expected coordination |
| `../04b_spec/output/` | 4 | Action signatures and outcome values |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command for compilation evidence |
| `../../../_config/package-and-layout.md` | 3 | Canonical test-source root and package layout |
| `../../../_config/test-framework.md` | 3 | Declares Gherkin or native track |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics, casing rules, payload rules |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School double-loop discipline |
| `../../../../../templates/feature.feature` | 3 | Gherkin output template (Gherkin track only) |
| `../../../../../templates/step-definitions.java` | 3 | Step-def skeleton template (Gherkin track only) |

## Process

Choose the track by reading `TEST_FRAMEWORK` from
`../../../_config/test-framework.md`. When `TEST_FRAMEWORK=CUCUMBER`,
use the Gherkin track. When `TEST_FRAMEWORK=NATIVE` or the file is
absent, use the native track.

### Gherkin track

1. **Derive** a Gherkin `.feature` file from `../../01_usecase/output/usecase.md`
   using the derivation rules in `../../../../../templates/feature.feature`:
   one `Feature` per use case, one `Scenario` (or `Scenario Outline`) per
   named scenario, one `Given`/`When`/`Then` step per precondition/trigger/
   postcondition.
2. **Derive** a step-definition class skeleton from
   `../../02b_chain-table/output/` (action chain per scenario) and
   `../04b_spec/output/` (action signatures, outcome enums) using the
   template at `../../../../../templates/step-definitions.java`.
   One method per chain-table row. `@Disabled` the skeleton or the
   Cucumber runner so the tests start red.
3. Add a Cucumber JUnit runner class (e.g. `CucumberTest.java`) under
   `APP_TEST_SOURCE_ROOT`, packaged under `APP_PACKAGE_ROOT`, pointing
   at the `.feature` file's resource directory.
4. Place the `.feature` file under
   `APP_TEST_SOURCE_ROOT/resources/features/<feature-name>.feature`.
   Place step-definition classes under `APP_PACKAGE_ROOT.steps`.

### Native track

1. For each named scenario in the use case, write a markdown spec:
   HTTP request → expected sequence of flow tokens → expected authored
   action chain → expected response.
2. Add a stub test under `APP_TEST_SOURCE_ROOT`, packaged under
   `APP_PACKAGE_ROOT`, starting `@Disabled` (red). Place it in the
   `flows` test location defined by
   `../../../_config/package-and-layout.md`.
3. One scenario = one markdown spec file + one stub test file. Do not
   replace required per-scenario files with a single consolidated
   artefact. A consolidated overview is optional only after all required
   per-scenario artefacts exist.

### Both tracks

Before claiming "red and ready", run the canonical build-and-test
command from `../../../_config/build-and-test.md` (or the targeted
equivalent documented there) and verify test compilation succeeds. At
this stage, acceptable red evidence is either
disabled/skipped tests (when stubs are intentionally `@Disabled`)
or failing tests if enabled; compilation errors are not
acceptable.

**Token chain rules (read `FLOW_TOKENS.md` in full before writing):**
- Outcome values MUST be SCREAMING_SNAKE_CASE, copied from the SPEC slice.
- Token count = number of rows in the chain table — no phantom intermediate tokens.
- Passwords and secrets MUST NOT appear in any token payload.

## Outputs

### Gherkin track

- `output/<feature-name>.feature` — one feature file per use case
- (Side effect:) `CucumberTest.java` (runner) + `<Feature>StepDefinitions.java` (skeleton, `@Disabled`)

### Native track

- `output/<scenario>-flow-test.md` per scenario
- (Side effect:) a stub test file under `reference-impl/<profile>/...`

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<scenario>-flow-test.md,…"  # one per scenario
```

- **verify_file_manifest.py:** `output/` contains exactly one
  flow-test markdown spec per scenario.

When the Gherkin track is active (`TEST_FRAMEWORK=CUCUMBER` in
`_config/test-framework.md` or `clad.properties`), also run the Gherkin derivation check:

```
python3 ../../../../quality-gate/verify_gherkin_derivation.py \
  --usecase ../../01_usecase/output/usecase.md \
  --feature output/login.feature \
  --sync-dir ../../03_syncs/output
```

- **verify_gherkin_derivation.py:** every use-case scenario has a
  matching Gherkin Scenario, every Scenario has Given/When/Then,
  response status codes match sync spec `then` clauses (per
  GHERKIN_INTEGRATION.md rules G1–G5, S1–S3, E1).

### Gherkin track

- Every named scenario in `usecase.md` has a corresponding Gherkin
  `Scenario` (happy path) or `Scenario Outline` (failure branches).
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

### Native track

- Every scenario has one flow-test markdown spec.
- Every scenario's markdown spec names an explicit expected authored
  action chain, not just a final response and token count.
- Every scenario has a corresponding stub flow test file under the
  configured `APP_TEST_SOURCE_ROOT` test tree.
- Every stub test is `@Disabled` (or red) and carries a `TODO` linking
  back to the scenario name.

### Both tracks

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

## Gate

Default human approval. After this gate, the outer loop is red.

## Next stage

→ [`../04d_concept-tdd/CONTEXT.md`](../04d_concept-tdd/CONTEXT.md) — Inner red→green per concept

To advance, the human says: **"Proceed to Stage 04d."**
