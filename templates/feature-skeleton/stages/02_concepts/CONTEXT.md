# Stage 02 — Concept specs

## Why this stage exists

Locks down each concept's full anatomy — state, action signatures with
outcomes, flow-token shape, operational principle — so that Stage 03
can name actions/outcomes precisely in syncs, Stage 04a can derive an
ORM schema from `state`, and Stage 04d can TDD the concept against a
fixed contract. Hard rule **R1** is enforced here: no concept names
another concept's state, actions, or types beyond opaque ids.

**Feeds:**

- `<Name>.concept.md` → 03 (`when`/`then` reference these action names + outcome enums), 03a (action existence and field declarations), 04a (`state` → relational schema), 04b (per-concept SPEC slice), 04d (concept TDD reads from this spec).

**Agent stance for this stage:** if you find yourself wanting to
import another concept's type, stop — that coordination belongs in a
sync, not in this file.

> **Note:** in Round 4 the choreography review (which concepts exist;
> what they own; how they fan out per scenario) was lifted into two
> upstream stages — `02a_responsibility-map/` and `02b_chain-table/`.
> This stage now does **only** the per-concept anatomy: full state,
> action signatures with outcomes, flow-token shape, and the
> operational principle.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Use case |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | The agreed concept set |
| `../02b_chain-table/output/` | 4 | The agreed action choreography (per scenario) — **read every file before naming any outcome** |
| `../00_actor-goal/output/actors.md` | 4 | For cross-stage check |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | Concept anatomy |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R2 |
| `../../../../templates/concept.md` | 3 | Output template |

## Process

For each concept already listed in
`02a_responsibility-map/output/responsibility-map.md`, draft
`<Name>.concept.md` per the template — full state, full action
signatures (inputs, outcomes, effect on state, flow-token fields),
and an operational principle.

**Outcome alignment is mandatory:** every action output name MUST
exactly match the outcome strings used in the approved chain tables in
`02b_chain-table/output/`. Open every chain table file before naming
any outcome. If you need an outcome the chain table did not name,
return to Stage 02b and amend the chain table first — do not invent
outcomes here.

**State and input discipline:** do not add state fields or action
inputs that have no basis in the chain table or responsibility map.
If a field is absent from both, raise it as an open question in the
concept's Notes section for the human reviewer.

R1 still applies: no concept names another concept's state, actions,
or types beyond opaque ids.

## Outputs

- `output/<Name>.concept.md` — one per concept in the responsibility map

## Verify

- The set of files in `output/` matches the set of concepts in
  `02a_responsibility-map/output/responsibility-map.md` exactly.
- **Outcome alignment:** every action output name in every concept file
  matches verbatim the outcome strings in the corresponding
  `02b_chain-table/output/` chain table. Check character-for-character —
  `AccountExists` and `EmailExists` are different names.
- **Input/state discipline:** no state field or action input appears
  that has no basis in the chain table or responsibility map.
- **Action discipline:** no action is declared that is not listed in
  `02a_responsibility-map/output/responsibility-map.md`.
- No concept names another concept's state, actions, or types.
- **Cross-stage check (back):** every actor in
  `00_actor-goal/output/actors.md` whose goal is in-scope appears in
  at least one concept's operational principle.

## Gate

Default human approval. **Do you agree with this step? Any
corrections before I continue?**

## Next stage

→ [`../03_syncs/CONTEXT.md`](../03_syncs/CONTEXT.md) — Synchronizations

To advance, the human says: **"Proceed to Stage 03."**
