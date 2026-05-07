# Stage 04b — SPEC

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../../../../../templates/spec.md` | 3 | Output template |

## Process

Derive the SPEC contract slice **mechanically** from each concept
spec: action signatures, outcome enums, flow-token shape. No prose
principle, no edge-case discussion — those stay in the concept spec.
The implementation in `04d` and `04e` compiles against these SPECs.

## Outputs

- `output/<Name>.spec.md` per concept

## Verify

- Every public action of every concept has a SPEC entry.
- Every SPEC entry's flow-token shape matches the concept's spec.
- **Cross-stage check (back):** the set of action names in `04b/output/`
  equals the set of action names in `02_concepts/output/`.

## Gate

Default human approval.
