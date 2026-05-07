# Stage 04c — Flow tests (UC-00-login)

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
