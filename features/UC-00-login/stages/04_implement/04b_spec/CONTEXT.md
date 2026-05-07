# Stage 04b — SPEC (UC-00-login)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../../../../../templates/spec.md` | 3 | Output template |

## Process

Mechanically derive the SPEC slice from each concept spec: action
signatures, outcome enums, flow-token shape. No prose, no edge-case
discussion (those stay in `02_concepts/`).

## Outputs

- `output/User.spec.md`
- `output/PasswordAuth.spec.md`
- `output/Session.spec.md`

## Verify

- Every public action in `02_concepts/output/` has a SPEC entry.
- **Cross-stage check (back):** the set of action names in `04b/output/` equals the set of action names in `02_concepts/output/`.

## Gate

Default.
