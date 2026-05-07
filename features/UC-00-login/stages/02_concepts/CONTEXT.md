# Stage 02 — Concept specs (UC-00-login)

> **Note:** Stages 02a (`responsibility-map`) and 02b (`chain-table`)
> precede this one. Read them first.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Use case |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | Agreed concept set |
| `../02b_chain-table/output/` | 4 | Agreed action choreography per scenario |
| `../00_actor-goal/output/actors.md` | 4 | Cross-stage check |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | Concept anatomy |
| `../../../../methodology/implementation/RULES.md` | 3 | R1, R2 |
| `../../../../templates/concept.md` | 3 | Output template |

## Process

For each row in `02a_responsibility-map/output/responsibility-map.md`,
draft `<Name>.concept.md` per the template — full state, full action
signatures (inputs, outcomes, effect on state, flow-token fields), and
operational principle. Outcomes must match the ones used in
`02b_chain-table/output/`. R1: no concept references another.

(`Web` is the bootstrap concept and does not get a `Web.concept.md` —
its anatomy is described in
[`../../../../methodology/architecture/WEB_CONCEPT.md`](../../../../methodology/architecture/WEB_CONCEPT.md).)

## Outputs

- `output/User.concept.md`
- `output/PasswordAuth.concept.md`
- `output/Session.concept.md`

## Verify

- One file per non-`Web` row in the responsibility map.
- Every action used in any `02b_chain-table/output/*-chain.md` is
  declared with the same outcome enum in the corresponding concept.
- No concept names another concept's state, actions, or types.
- **Cross-stage check (back):** the UC-00 actor (`User`) appears in
  at least one concept's operational principle.

## Gate

Default human approval. **Do you agree with this step? Any
corrections before I continue?**
