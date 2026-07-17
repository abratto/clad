# Stage 02 — Concept specs (UC-00-login)

## Why this stage exists

Locks down each concept's full anatomy — state, action signatures with
outcomes, flow-token shape, operational principle — so that Stage 03
can name actions/outcomes precisely in syncs, Stage 03b can derive a
conceptual data model from `state`, and Stage 04d can TDD the concept against a
fixed contract. Hard rule **R1** is enforced here: no concept names
another concept's state, actions, or types beyond opaque ids.

**Feeds:**

- `<Name>.concept.md` → 03 (`when`/`then` reference these action names + outcome enums), 03a (action existence and field declarations), 03b (`state` → conceptual data model), 04b (per-concept SPEC slice), 04d (concept TDD reads from this spec).

**Agent stance for this stage:** if you find yourself wanting to
import another concept's type, stop — that coordination belongs in a
sync, not in this file.

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
| Skill: `clad-concept-design` | 3 | Concept design reference |
| `../../../../templates/concept.md` | 3 | Output template |

## Process

For each row in `02a_responsibility-map/output/responsibility-map.md`,
draft `<Name>.concept.md` per the template — concept header with type
parameters, purpose, state (paper-syntax relational notation with
multiplicity annotations), full action signatures (inputs, outcomes,
effect on state, flow-token fields), and operational principle.
Outcomes must match the ones used in `02b_chain-table/output/`.
R1: no concept references another.

(`Web` is the bootstrap concept and does not get a `Web.concept.md` —
its anatomy is described in
[`../../../../methodology/architecture/WEB_CONCEPT.md`](../../../../methodology/architecture/WEB_CONCEPT.md).)

## Pre-condition (agent must verify before starting)

```
python3 ../../../../quality-gate/verify_gate_approval.py --feature ../../ --required-gates 1
```

Gate 1 (Requirements) must be approved before Stage 02 begins. If this
fails, return to Stage 02b and complete gate approval.

## Outputs

- `output/User.concept.md`
- `output/PasswordAuth.concept.md`
- `output/Session.concept.md`

## Verify

### Automated checks

```
python3 ../../../../quality-gate/verify_action_chain.py \
  --resp-map ../02a_responsibility-map/output/responsibility-map.md \
  --chain-dir ../02b_chain-table/output \
  --concept-dir output \
  --sync-dir ../03_syncs/output \
  --dep-dir ../03a_dependency-review/output \
  --spec-dir ../04_implement/04b_spec/output
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output \
  --expected "User.concept.md,PasswordAuth.concept.md,Session.concept.md"
```

- **verify_action_chain.py:** every action used in chain tables flows consistently.
- **verify_file_manifest.py:** `output/` contains exactly one `.concept.md` per business concept.

### Semantic checks (human)

- One file per non-`Web` row in the responsibility map.
- Every action used in any `02b_chain-table/output/*-chain.md` is
  declared with the same outcome enum in the corresponding concept.
- No concept names another concept's state, actions, or types.
- **Cross-stage check (back):** the UC-00 actor (`User`) appears in
  at least one concept's operational principle.

## Gate

Auto-advances (next human gate: Stage 03b). The quality-gate scripts
(`verify_action_chain.py`, `verify_file_manifest.py`) must all pass
before advancing.

## Next stage

→ [`../03_syncs/CONTEXT.md`](../03_syncs/CONTEXT.md) — Synchronizations

The agent proceeds to Stage 03 without a human gate.
