# Stage 04c — Flow tests (UC-00-login)

## Why this stage exists

The **outer red** of the outside-in TDD double-loop. One failing flow
test per use-case scenario, each asserting (a) the HTTP request, (b)
the expected sequence of flow tokens, and (c) the response. These tests
stay red through 04d (concept TDD) and go **green at the end of 04e**
(sync TDD). They are the executable form of the use case — if they
pass, the scenario passes; if they don't exist, the scenario isn't
covered.

**Feeds:**

- `login.feature` → 04e (when the last sync's tests go green, this too); 05 (scenario names cross-reference in trace).
- `LoginStepDefinitions.java` → the outer loop of TDD itself.

**Agent stance for this stage:** these tests must read like the use
case. If they read like a unit test, you are testing the wrong layer.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../01_usecase/output/usecase.md` | 4 | Scenarios to test |
| `../../03_syncs/output/` | 4 | Expected coordination |
| `../04b_spec/output/` | 4 | Action signatures |
| `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md` | 4 | Required when present; external adapter contract for `@contract` scenarios |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |
| `../../../../../methodology/architecture/GHERKIN_INTEGRATION.md` | 3 | Gherkin derivation rules |

## Process

For the login use case, produce a Gherkin `.feature` file with one
`Scenario` per use-case scenario (`successful-login`, `wrong-password`,
`unknown-user`, `lockout`). Derive a `LoginStepDefinitions.java` skeleton
from the chain-table rows, annotated `@Disabled`. Flow tests stay red
until the end of `04e`.

If `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md`
exists, add at least one `@contract` scenario per HTTP endpoint. These
scenarios assert exact JSON paths, field types constrained by the
external contract, and the primary failure path's exact error envelope
shape. Keep these distinct from `@happy-path` and `@failure-path`
intent scenarios.

> A historical native-track markdown spec (`login-flow-test.md`) is
> preserved in `output/` for reference — see `output/_NOTE.md`.

## Outputs

- `output/login.feature` — Gherkin feature file with all 4 scenarios
- (Side effect:) `LoginStepDefinitions.java` skeleton + `CucumberTest.java` runner

## Verify

- Each use-case scenario has a Gherkin `Scenario` in `login.feature`.
- When `port-spec.md` exists, every HTTP endpoint has at least one
  `@contract` scenario with exact JSON path/type/envelope assertions.
- Step-definition methods map 1:1 to chain-table rows.
- Compiled flow tests are `@Disabled` (or red) — not green.
- **Cross-stage check (back):** the predicted token chain matches the syncs in `03_syncs/output/`.

## Gate

Default. After this gate the outer loop is red.

## Next stage

→ [`../04d_concept-tdd/CONTEXT.md`](../04d_concept-tdd/CONTEXT.md)

To advance, the human says: **"Proceed to Stage 04d."**
