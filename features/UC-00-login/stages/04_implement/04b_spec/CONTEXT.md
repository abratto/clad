# Stage 04b — SPEC (UC-00-login)

## Why this stage exists

The SPEC is the **machine-checkable slice** of each concept spec —
action signatures, outcome enums, flow-token shape — with the prose
principle and edge-case discussion stripped out. 04d and 04e compile
against the SPECs, not against the prose. Without 04b the inner-loop
tests would have to re-derive the contract from prose every time the
spec changes.

**Feeds:**

- `<Name>.spec.md` → 04c (flow tests assert SPEC-level signatures), 04d (concept TDD compiles against SPEC), 04e (sync TDD references SPEC action enums).

**Agent stance for this stage:** mechanical extraction only. If the
SPEC needs an action that isn't in the concept spec, the defect is
upstream (Stage 02), not here.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md` | 4 | Required when present; external adapter response-shape contract |
| `../../../../../templates/spec.md` | 3 | Output template |

## Process

Mechanically derive the SPEC slice from each concept spec: action
signatures, outcome enums, flow-token shape. No prose, no edge-case
discussion (those stay in `02_concepts/`).

If `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md`
exists, add a separate **Response shapes** section to the relevant SPEC
output. Derive it from the port spec, not from local implementation
preference. It must name exact JSON paths, field types, wrappers, and
error envelope values required by the external contract.

## Outputs

- `output/User.spec.md`
- `output/PasswordAuth.spec.md`
- `output/Session.spec.md`

## Verify

- Every public action in `02_concepts/output/` has a SPEC entry.
- **Cross-stage check (back):** the set of action names in `04b/output/` equals the set of action names in `02_concepts/output/`.
- When `port-spec.md` exists, SPEC output includes exact response shape
	examples for each relevant HTTP endpoint: JSON paths, field types,
	wrappers, and error envelope values.

## Gate

Auto-advances (next human gate: Stage 04c).

## Next stage

→ [`../04c_flow-tests/CONTEXT.md`](../04c_flow-tests/CONTEXT.md) — Outer red (flow tests)

To advance, the human says: **"Proceed to Stage 04c."**
