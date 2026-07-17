# Gherkin Integration — outer-red BDD flow tests

This document is the **stable reference** for CLAD's Gherkin/Cucumber
integration. It answers three questions for agents and humans:

1. **What** is the Gherkin track?
2. **How** are Gherkin artefacts mechanically derived from upstream
   CLAD artefacts?
3. **How** does the Gherkin track interact with existing CLAD stages
   (04c, 04e, 05)?

Cucumber/BDD is the **sole outer-red flow-test track** in CLAD. Gherkin
`.feature` files are the single source of truth for flow assertions,
replacing earlier markdown flow-test specs with executable scenarios
that go green at the end of Stage 04e.

### Gherkin track artefact chain

```
  01_usecase/output/usecase.md ──────┐
                                     ├──→ 04c: login.feature
  02b_chain-table/output/ ───────────┤         (Gherkin scenarios)
                                     ├──→ 04c: LoginStepDefinitions.java
  04b_spec/output/*.spec.md ─────────┤         (step-definition skeletons)
                                     │
  03_syncs/output/*.sync.md ─────────┘
         (response body literals)
```

The `.feature` file is a **derived view** — it should be regenerated
when the use case changes, not hand-edited. Step-definition skeletons
are derived from chain-table rows and SPEC outcome enums.

---

## 2. Cucumber/BDD standard

Cucumber/BDD is the sole outer-red flow-test track. No config file or
track selection is needed — every CLAD feature uses Gherkin `.feature`
files and step-definition classes at Stage 04c.

| Stage | Effect |
|---|---|
| 04c | Produces Gherkin `.feature` file + step-definition skeleton |
| 04e-red | Every `.feature` scenario must have a sync test |
| 04e-green | Cucumber runner executes all scenarios |
| 05 | Gherkin scenario names cross-reference in trace |

---

## 3. Derivation rules: usecase.md → .feature

> Rules G1–G5 below. Templates at `templates/feature.feature`.

These rules are documented in the template at
[`../../templates/feature.feature`](../../templates/feature.feature)
as HTML comments. They are reproduced here as a structured reference.

### Rule G1 — Feature header

| `.feature` element | Source in `usecase.md` | Rule |
|---|---|---|
| `Feature: <name>` | H1 `# UC-XX — <name>` | Use the name after the em-dash |
| `@UC-XX` | UC-XX folder name | Extract the UC number |
| `As a <actor>` | `## Actors` | First primary actor listed (bold text before the em-dash) |
| `I want <goal>` | `## Operational principle` | First sentence, stop at the period |
| `So that <rationale>` | `## Operational principle` | Remainder after the first sentence |

### Rule G2 — Scenario structure

| `.feature` element | Source in `usecase.md` | Rule |
|---|---|---|
| `@<scenario-name>` | `### Scenario: <name>` | Hyphenate the scenario name |
| `@happy-path` | Postconditions — Success ≠ "Not applicable" | Add when the scenario has Success postconditions |
| `@failure-path` | Postconditions — Success = "Not applicable" | Add when the scenario is a failure branch |
| `@no-state-change` | Postconditions — Failure contains "no state is modified" | Add when the use case asserts no state change |
| `Scenario: <name>` | `### Scenario: <name>` | 1:1 — one named scenario per Gherkin Scenario |
| `Given <precondition>` | `Pre-conditions:` bullet | One `Given` per bullet. Omit "A"/"The" article prefix — Gherkin steps read as declarative state |
| `When <trigger>` | Main flow **step 1 only** | Always the primary actor's action. Never a system action. Use the exact HTTP verb and route when present |
| `Then <response assertion>` | `Expected outcomes:` bullet | One `Then` per observable outcome. Prefer `response status is <code>` and `response body contains <text>` |
| `Then <state assertion>` | `Postconditions — Success:` / `Postconditions — Failure:` | Use the "no state is modified" form for Failure assertions |

### Rule G3 — Response assertions

Assert the response using the **exact literals** from the sync spec's
`then` clause in `03_syncs/output/`. The sync spec is authoritative
for what the system actually returns.

| `03_syncs/output/` field | `.feature` assertion |
|---|---|
| `Web.respond(status=401)` | `Then the response status is 401` |
| `Web.respond(status=200)` | `Then the response status is 200` |
| `body={ message: "..." }` | `Then the response body contains "..."` |
| `body={ sessionToken: ... }` | `Then the response body contains "sessionToken"` |

### Rule G4 — Failure-branch tagging

Three distinct failure scenarios, distinguished by postconditions:

| Scenario type | Tag | Then assertions |
|---|---|---|
| Happy-path failure (e.g. wrong password) | `@failure-path` | Status check + body check. State assertion on the concept whose counter incremented. |
| No-state-change failure (e.g. unknown user) | `@failure-path @no-state-change` | Status check + body check + `And no state is modified in any concept`. |
| Lockout / blocking failure (e.g. account locked) | `@failure-path` | Status check + body check (distinct message). State assertion on the lockout expiry. |

### Rule G5 — Scenario Outlines for extension branches

When the use case has `Extensions:` with branching conditions that
share the same trigger, collapse them into a `Scenario Outline`:

```
Scenario Outline: <scenario-name> — <branch-condition>
  Given <shared precondition>
  When the user submits <route> with "<field1>" and "<field2>"
  Then the response status is <status>
  And the response body contains "<message>"
  And the runtime token chain matches:<expected chain>

  Examples:
    | branch-condition | field1 | field2 | status | message | expected chain |
    | <condition 1>    | <val>  | <val>  | <code> | <msg>   | <seq>          |
    | <condition 2>    | <val>  | <val>  | <code> | <msg>   | <seq>          |
```

Each `Examples:` row corresponds to one extension branch. The
`<message>` literal is copied from the matching sync spec's `then`
clause.

---

## 4. Derivation rules: chain tables → step-definition methods

These rules are documented in the template at
[`../../templates/step-definitions.java`](../../templates/step-definitions.java).

### Rule S1 — One method per chain-table row

| Chain-table column | Step-definition element |
|---|---|
| `#` (row number) | Method ordering — chain-table row 1 is the first method called |
| `When` (e.g. `Web.handle[Routed]`) | Method trigger condition — determines when this method is invoked |
| `Then` (e.g. `User.lookupByUsername`) | The concept action the method invokes |
| `Inputs` (e.g. `username`) | Method parameters |
| `Outcome` (e.g. `Found(userId)`) | Expected outcome — documented in Javadoc, asserted in the step |
| `Why this step` | Method Javadoc comment |

### Rule S2 — Row mapping

| Chain-table row | Maps to Cucumber annotation | Purpose |
|---|---|---|
| Row 1: `Web/request → Web.handle` | `@When` | The HTTP trigger. One `@When` per scenario with `{string}` parameters for request data. |
| Middle rows: `Web.handle → Concept.action` | Not directly annotated (called by syncs) | The sync engine invokes these. Documented in the `@When` method Javadoc as the expected token chain. |
| Last row: `Concept.action → Web.respond` | `@Then` | The response assertion. Status code and body content from the sync spec. |

### Rule S3 — Token chain assertion

The `@Then("the runtime token chain matches:")` step asserts the
sequence of emitted flow tokens equals the chain-table row sequence.
Each token's `action` and `outcome` fields must match a chain-table
row's `Then` action name and `Outcome` value (SCREAMING_SNAKE_CASE).

```
Chain-table row 2: Web.handle[Routed] → User.lookupByUsername → Found(userId)
Chain-table row 3: User.lookupByUsername[Found] → PasswordAuth.check → Ok
Chain-table row 4: PasswordAuth.check[Ok] → Session.grant → Granted(sessionId)

Runtime tokens:
  [
    { action: "User.lookupByUsername", outcome: "FOUND" },
    { action: "PasswordAuth.check",     outcome: "OK" },
    { action: "Session.grant",          outcome: "GRANTED" }
  ]
```

---

## 5. Derivation rules: SPECs → outcome enums

### Rule E1 — SCREAMING_SNAKE_CASE

Outcome enum values in step-definition assertions are copied **verbatim**
from the SPEC slice at `04b_spec/output/<Name>.spec.md`. Each SPEC
action section lists its `Outcomes (enum):` field. Use those exact
values.

| SPEC file | Action | Enum values | Used in |
|---|---|---|---|
| `User.spec.md` | `lookupByUsername` | `FOUND`, `NOT_FOUND` | Token chain assertions |
| `PasswordAuth.spec.md` | `check` | `OK`, `BAD_PASSWORD`, `LOCKED` | Token chain assertions + Given seed logic |
| `Session.spec.md` | `grant` | `GRANTED` | Token chain assertions |

---

## 6. Cross-stage consistency checks

### Stage 04c verify

- Every named scenario in `usecase.md` has a corresponding Gherkin
  `Scenario` or `Scenario Outline`.
- Every `Given` step traces to a use-case `Pre-conditions:` bullet.
- Every `When` step traces to a use-case Main flow step 1.
- Every `Then` step traces to an `Expected outcomes:` or `Postconditions:`.
- Every step-definition method body references a chain-table row's
  `Then` action name.
- Outcome values are SCREAMING_SNAKE_CASE, matching `04b_spec/output/`.
- The `.feature` file parses without syntax errors
  (`cucumber --dry-run` or profile equivalent).
- No Gherkin step exists without a corresponding use-case element.
- **Automated:** `verify_gherkin_derivation.py` enforces rules G1–G5, S1–S3, E1.
- **Automated:** `verify_step_definition_parity.py` checks that every
  step has a matching method with a non-empty body — catches stubs.
- **Automated:** `verify_step_definition_derivation.py` checks that every
  business-concept action name from the chain tables appears in at least
  one step-definition method body — catches methods that compile but
  don't exercise the chain-table action sequence.

### Stage 04e-red verify

- Every Gherkin `Scenario` has at least one sync test row in the
  derivation map.
- The sync test's trigger pattern matches the `When` step's expected
  token-chain root.

### Stage 04e-green verify

- All Gherkin scenarios are green via the Cucumber runner.
- Cucumber report (HTML/JSON) is captured as gate evidence.
- The runtime token chain observed by each passing scenario matches
  the chain-table row sequence.
- Any intentionally deferred scenario is honestly red and documented as
  deferred — this is a coverage signal, not a hidden pass.
- **Automated:** `verify_cucumber_green.py` runs the test command and
  fails on any undefined, pending, skipped, or failing Cucumber
  scenario. The gate does not pass until every Gherkin scenario is green.

### Stage 05 verify

- Every Gherkin scenario name appears as a heading or cross-reference
  in `trace.md`.
- Cucumber report (if present) shows 0 failed scenarios for the
  scenarios exercised in `smoke.md`.
- The Gherkin scenarios provide no additional coverage beyond what the
  use case already defines — they are a derived view, not a new
  contract.

---

## 7. Worked example: UC-00-login

The reference implementation under
[`../../reference-impl/java-micronaut-jena/`](../../reference-impl/java-micronaut-jena/)
contains a complete worked example of the Gherkin track:

| Artefact | File | Derivation source |
|---|---|---|
| `.feature` file | `src/test/resources/features/login.feature` | `features/UC-00-login/stages/01_usecase/output/usecase.md` (scenarios, preconditions, triggers, postconditions) + `stages/03_syncs/output/` (response body literals) |
| Step definitions | `src/test/java/.../steps/LoginStepDefinitions.java` | `stages/02b_chain-table/output/*-chain.md` (row 1 → `@When`, last row → `@Then`, middle rows → token chain) + `stages/04_implement/04b_spec/output/` (outcome enums) |
| Cucumber runner | `src/test/java/.../steps/CucumberTest.java` | `@Suite` + `@SelectClasspathResource("features")` |

The step definitions use **lazy server initialisation** (no Cucumber
`@BeforeAll` hook) to avoid Cucumber lifecycle issues. The
`EmbeddedServer` starts when the first `@Given("the system is running")`
step executes, via `ensureServerRunning()`.

---

## 8. Agent instructions summary

When operating at Stage 04c, follow this checklist:

```
□ 1. Read 01_usecase/output/usecase.md → extract:
     - Feature name (H1)
     - Primary actor (## Actors)
     - Goal + rationale (## Operational principle)
     - Named scenarios (### Scenario: <name>)
     - Pre-conditions, trigger, expected outcomes, postconditions
     - Extension branches
□ 3. Read 02b_chain-table/output/*-chain.md → extract action sequence
□ 4. Read 04b_spec/output/*.spec.md → extract outcome enums
□ 5. Read 03_syncs/output/*.sync.md → extract response body literals
□ 6. Derive the .feature file using Rules G1–G5
□ 7. Derive the step-definition class using Rules S1–S3 and E1
□ 8. Write the Cucumber runner class (CucumberTest.java)
□ 9. Run the canonical build-and-test command → compilation succeeds
□ 10. Verify: every Gherkin element traces to an upstream artefact
```

### What not to do

- Do not hand-edit a `.feature` file without regenerating from the use
  case. It is a derived view. Hand-edits cause spec–test drift.
- Do not add step-definition methods that don't map to a chain-table
  row. Every step must trace to a use-case element.
- Do not add imperative branching or domain logic in step definitions.
  Conditional behavior belongs in concept outcomes and sync triggers.
- Do not use Cucumber `@BeforeAll` / `@AfterAll` — use lazy
  initialisation in a `@Given` step instead (Cucumber's `@BeforeAll` is
  incompatible with standard step-definition class loading).
- Do not copy features from another UC folder. Derive from this
  feature's own use case and chain tables.

---

## 9. References

| Resource | Location | Purpose |
|---|---|---|
| Gherkin template | [`../../templates/feature.feature`](../../templates/feature.feature) | Output template with derivation rules |
| Step-def skeleton template | [`../../templates/step-definitions.java`](../../templates/step-definitions.java) | Step-def derivation rules |
| 04c CONTEXT | [`../../templates/feature-skeleton/stages/04_implement/04c_flow-tests/CONTEXT.md`](../../templates/feature-skeleton/stages/04_implement/04c_flow-tests/CONTEXT.md) | Stage process, verify items |
| Worked example | [`../../reference-impl/java-micronaut-jena/src/test/resources/features/login.feature`](../../reference-impl/java-micronaut-jena/src/test/resources/features/login.feature) | Real `.feature` file |
| Worked example | [`../../reference-impl/java-micronaut-jena/src/test/java/com/example/app/steps/LoginStepDefinitions.java`](../../reference-impl/java-micronaut-jena/src/test/java/com/example/app/steps/LoginStepDefinitions.java) | Real step-definition class |
