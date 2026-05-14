# Workflow overlay — PLANNING

> **Status: optional.** This overlay adds lightweight intake and sequencing
> checks before starting a new feature. It does not change CLAD stage
> semantics and does not replace Stage 00.

## Why this overlay exists

Natural-language prompts like "Let's work on a new feature" are useful,
but they can skip a short planning check that prevents churn:

- Is this feature the highest-priority next item?
- Is another feature already in progress that should finish first?
- Are there unresolved dependencies that would block Stage 01+?

This overlay adds a minimal decision point before Stage 00.

## Inputs

- `ROADMAP.md` (if present)
- `plan-board.md` (if present; see template in `templates/plan-board.md`)
- Active feature `RESUME.md` files (if present)
- Stage 00 outputs if present:
  `features/_system/stages/00_actor-goal/output/actors.md` and
  `features/_system/stages/00_actor-goal/output/goals.md`

## Artifact existence checklist

Check these paths in this order before deciding what to do:

1. `features/_system/stages/00_actor-goal/output/actors.md`
2. `features/_system/stages/00_actor-goal/output/goals.md`
3. `plan-board.md`
4. `ROADMAP.md`

## Project states (routing matrix)

Use this matrix before sequencing work:

1. **Project start (no actor/goals yet)**
  - Condition: Stage 00 output files do not exist.
  - Action: skip planning and run Stage 00 first.
  - Result: produce `actors.md` and `goals.md`, then return to planning
    intake if sequencing is needed.

2. **Project started (actor/goal list defined, no plan yet)**
  - Condition: Stage 00 outputs exist, `plan-board.md` missing.
  - Action: planning is optional.
  - Result: either (a) pick an existing approved goal and continue CLAD
    stages directly, or (b) create `plan-board.md` and sequence goals.

3. **Project started (actor/goal list defined and plan created)**
  - Condition: Stage 00 outputs exist and `plan-board.md` exists.
  - Action: run intake checks against priority, dependency, and active `doing`
    work before starting another feature.
  - Result: `start now`, `queue next`, or `blocked`.

4. **Project started (goals changed after plan was created)**
  - Condition: new/edited goals are present but `plan-board.md` is stale.
  - Action: run a plan-drift check and update plan rows/decisions.
  - Result: revised sequence that reflects current goals.

## Plan-drift check

Run this whenever Stage 00 outputs change after planning exists:

1. Compare current `goals.md` to `plan-board.md` feature rows.
2. Add rows for newly accepted goals.
3. Re-check dependencies and reorder priority if needed.
4. Append an intake decision row documenting why ordering changed.

## Worked examples (one-liners)

1. **No Stage 00 outputs yet**
  - Prompt: "Let's work on a new feature"
  - Agent action: run Stage 00 first; no sequencing yet.

2. **Stage 00 outputs exist, no plan-board**
  - Prompt: "Let's work on a new feature"
  - Agent action: ask whether to sequence now or start a specific goal.

3. **Stage 00 outputs and plan-board exist**
  - Prompt: "Let's work on a new feature"
  - Agent action: check active `doing` row + dependency fit, then start/queue.

4. **Goals changed after planning**
  - Prompt: "Let's work on a new feature"
  - Agent action: update plan-board first (plan-drift), then start/queue.

## New-feature intake protocol

When the human says "Let's work on a new feature" (or equivalent):

1. Detect project state from the matrix above.
2. If no Stage 00 actor/goal outputs exist, run Stage 00 now and stop at
  the gate.
3. If actor/goal outputs exist, read `ROADMAP.md` and `plan-board.md`
  (if present).
4. If sequencing is unclear, ask exactly one planning question.
5. If `plan-board.md` is missing and the human wants sequencing, create it
  from current goals and known dependencies.
6. If goals changed since planning, run the plan-drift check.
7. Route to the next approved action: start a specific goal, queue it, or
  wait for a blocker.

## Suggested one-question prompts

Use one, and only one, when needed:

- "Should this become the active feature now, or queue behind UC-XX?"
- "Do you want to finish the current Stage NN gate first, then start this?"
- "This appears blocked by <dependency>; still start Stage 00 now?"

## Decision outcomes

- **Start now:** proceed to Stage 00 immediately.
- **Queue next:** record in `plan-board.md`, do not run Stage 00 yet.
- **Blocked:** record blocker and prerequisite in `plan-board.md`; wait.

## Guardrails

- Do not create a `features/UC-XX-<slug>/` folder before Stage 00 is approved.
- Do not run two UC features as active `doing` simultaneously unless the human
  explicitly overrides this.
- Planning never invents actors/goals that were not accepted through Stage 00.
- Planning is optional once goals exist; teams may still pick a goal directly.

## Recommended cadence

- Update `plan-board.md` when priorities change.
- Re-check planning intake at each "new feature" request.
- Keep planning artifacts small and editable in one screen.
