# Stage 04b — SPEC

## Why this stage exists

The SPEC is the **machine-checkable slice** of each concept spec —
action signatures, outcome enums, flow-token shape — with the prose
principle and edge-case discussion stripped out. 04d and 04e compile
against the SPECs, not against the prose. Without 04b the inner-loop
tests would have to re-derive the contract from prose every time
the spec changes.

**Feeds:**

- `<Name>.spec.md` → 04c (flow tests assert SPEC-level signatures), 04d (concept TDD compiles against SPEC), 04e (sync TDD references SPEC action enums).

**Agent stance for this stage:** mechanical extraction only. If the
SPEC needs an action that isn't in the concept spec, the defect is
upstream (Stage 02), not here.

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
