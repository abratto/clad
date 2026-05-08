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

- `<scenario>-flow-test.md` → 04e (when the last sync's tests go green, these tests must too); 05 (the runtime token chain captured by these tests is the back-trace evidence).
- the stub test files in `reference-impl/<profile>/.../flows/` → the outer loop of TDD itself.

**Agent stance for this stage:** these tests must read like the use
case. If they read like a unit test, you are testing the wrong layer.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../01_usecase/output/usecase.md` | 4 | Scenarios to test |
| `../../03_syncs/output/` | 4 | Expected coordination |
| `../04b_spec/output/` | 4 | Action signatures |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |

## Process

For each named scenario in the use case, write a flow-test markdown
spec (HTTP request → expected sequence of flow tokens → expected
response) and a stub Java test under
`reference-impl/java-micronaut-jena/src/test/java/com/example/app/flows/`
starting `@Disabled`. The tests go green at the end of `04e`.

## Outputs

- `output/login-flow-test.md` — covers `successful-login`, `wrong-password`, `unknown-user`, `lockout`
- (Side effect:) `LoginFlowTest.java` (`@Disabled`) under the Java profile

## Verify

- Each scenario has an entry in the markdown spec.
- The stub Java test is `@Disabled` and links back to the markdown.
- **Cross-stage check (back):** the predicted token chain matches the syncs in `03_syncs/output/` (no surprise tokens).

## Gate

Default. After this gate the outer loop is red.

## Next stage

→ [`../04d_concept-tdd/CONTEXT.md`](../04d_concept-tdd/CONTEXT.md) — Inner red→green per concept

To advance, the human says: **"Proceed to Stage 04d."**
