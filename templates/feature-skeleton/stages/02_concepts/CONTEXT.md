# Stage 02 — Concepts

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | The use case to satisfy |
| `../00_actor-goal/output/actors.md` | 4 | For cross-stage check |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | Concept anatomy |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R2 |
| `../../../../templates/concept.md` | 3 | Output template |

## Process

Identify the concepts the feature requires (one user-facing capability
each). For each, draft `<Name>.concept.md` per the template — state,
actions (with outcomes and flow-token contributions), and an
operational principle. No concept references another (R1).

## Outputs

- `output/<Name>.concept.md` — one per concept

## Verify

- No concept names another concept's state, actions, or types beyond opaque ids.
- Every action lists its outcomes and flow-token fields.
- **Cross-stage check (back):** every actor in
  `00_actor-goal/output/actors.md` whose goal is in-scope appears in at
  least one concept's operational principle (as the actor whose
  perspective the principle takes).
- The set of concepts together covers every observable in the use case.

## Gate

Default human approval. This is the most common place to catch
over-fused or under-split concepts.
