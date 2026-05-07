# Stage 02 — Concepts

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | The use case to satisfy |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | Concept anatomy |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules (R1, R2) |
| `../../../../templates/concept.md` | 3 | Output template |

## Process

Identify the concepts UC-00 requires (one capability each). Draft
`<Name>.concept.md` per the template for each. Each must have state,
actions (with outcomes and flow-token contributions), and an
operational principle. No concept may reference another.

## Outputs

- `output/User.concept.md`
- `output/PasswordAuth.concept.md`
- `output/Session.concept.md`

## Verify

- No concept names another concept's state or actions.
- Every action lists its outcomes and its flow-token fields.
- The three concepts together cover every observable in the use case.
