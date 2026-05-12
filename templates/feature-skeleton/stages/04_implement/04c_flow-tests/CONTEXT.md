# Stage 04c — Flow tests (outer red)

## Why this stage exists

The **outer red** of the outside-in TDD double-loop. One failing flow
test per use-case scenario, each asserting (a) the HTTP request, (b)
the expected sequence of flow tokens, and (c) the response. These tests
stay red through 04d (concept TDD) and go **green at the end of 04e**
(sync TDD). They are the executable form of the use case — if they
pass, the scenario passes; if they don't exist, the scenario isn't
covered.

**Feeds:**

- `<scenario>-flow-test.md` → 04e (when the last sync's tests go green, these tests must too); 05 (the runtime token chain captured by these tests is the back-trace evidence).
- the stub test files in `reference-impl/<profile>/.../flows/` → the outer loop of TDD itself.

**Agent stance for this stage:** these tests must read like the use
case. If they read like a unit test, you are testing the wrong layer.
Read `methodology/implementation/TDD.md` before writing anything.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../01_usecase/output/usecase.md` | 4 | Scenarios to test |
| `../../03_syncs/output/` | 4 | Expected coordination |
| `../04b_spec/output/` | 4 | Action signatures and outcome values |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics, casing rules, payload rules |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School double-loop discipline |

## Process

For each named scenario in the use case, write the **outer** test as a
markdown spec: HTTP request → expected sequence of flow tokens →
expected response. Then add a stub test under
`reference-impl/<profile>/src/test/.../flows/<Scenario>FlowTest.java`
(or the profile's equivalent), starting `@Disabled` (red). The test
goes green at the end of `04e`.

**Token chain rules (read `FLOW_TOKENS.md` in full before writing):**
- Outcome values MUST be SCREAMING_SNAKE_CASE, copied from the SPEC slice.
- Token count = number of rows in the chain table — no phantom intermediate tokens.
- Passwords and secrets MUST NOT appear in any token payload.

## Outputs

- `output/<scenario>-flow-test.md` per scenario
- (Side effect, listed here for completeness:) a stub test file under `reference-impl/<profile>/...`

## Verify

- Every scenario has one flow-test markdown spec.
- Every stub test is `@Disabled` (or red) and carries a `TODO` linking back to the scenario name.
- All outcome values are SCREAMING_SNAKE_CASE.
- No passwords or secrets appear in any token payload.
- Token count per scenario equals the number of rows in the corresponding chain table.
- **Cross-stage check (back):** the flow-test markdown's expected token
  chain matches the syncs in `03_syncs/output/` (no surprise tokens).

## Gate

Default human approval. After this gate, the outer loop is red.

## Next stage

→ [`../04d_concept-tdd/CONTEXT.md`](../04d_concept-tdd/CONTEXT.md) — Inner red→green per concept

To advance, the human says: **"Proceed to Stage 04d."**
