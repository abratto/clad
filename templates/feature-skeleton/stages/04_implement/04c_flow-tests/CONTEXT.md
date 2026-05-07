# Stage 04c — Flow tests (outer red)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../01_usecase/output/usecase.md` | 4 | Scenarios to test |
| `../../03_syncs/output/` | 4 | Expected coordination |
| `../04b_spec/output/` | 4 | Action signatures |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |

## Process

For each named scenario in the use case, write the **outer** test as a
markdown spec: HTTP request → expected sequence of flow tokens →
expected response. Then add a stub test under
`reference-impl/<profile>/src/test/.../flows/<Scenario>FlowTest.java`
(or the profile's equivalent), starting `@Disabled` (red). The test
goes green at the end of `04e`.

## Outputs

- `output/<scenario>-flow-test.md` per scenario
- (Side effect, listed here for completeness:) a stub test file under `reference-impl/<profile>/...`

## Verify

- Every scenario has one flow-test markdown spec.
- Every stub test is `@Disabled` (or red) and carries a `TODO` linking back to the scenario name.
- **Cross-stage check (back):** the flow-test markdown's expected token
  chain matches the syncs in `03_syncs/output/` (no surprise tokens).

## Gate

Default human approval. After this gate, the outer loop is red.
