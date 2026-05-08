# Stage 00 — Actor / Goal

## Why this stage exists

This stage answers *"who wants what."* Without it, every later stage
is solving for an unstated user, and the use case drifts. The human's
brief alone is too soft to plan against; turning it into a confirmed
actor list and goal list is what lets the rest of the loop be
mechanical.

**Feeds:**

- `actors.md` → Stage 01 (verbatim actor list in `usecase.md`); Stage 02a (every in-scope actor must be represented by ≥1 concept).
- `goals.md` → Stage 01 (every in-scope goal becomes ≥1 named scenario; out-of-scope goals lift into the use case's *Out of scope* section).

**Agent stance for this stage:** propose, ask ≤5 questions, iterate. Do
not write `actors.md` / `goals.md` until the human signals agreement.

## Inputs

| Path | Layer | Why |
|---|---|---|
| (the human's brief) | — | Source of intent |
| `../../../../templates/actors.md` | 3 | Output template |
| `../../../../templates/goals.md` | 3 | Output template |
| `../../../../methodology/implementation/STAGES.md` | 3 | §"Stage 00" — collaboration semantics |

## Process

**This stage is multi-turn and collaborative.** The agent:

1. **Proposes** an initial actor/goal list inferred from the human's brief.
2. **Asks at most 5 clarifying questions** in a single turn.
3. Iterates with the human until they signal agreement.
4. **Only then** writes `actors.md` and `goals.md` per the templates.

The agent does not invent goals the human has not confirmed. If the
brief is too thin to propose anything, the agent asks for more context
before drafting.

## Outputs

- `output/actors.md` — one row per actor (name, role, primary concerns)
- `output/goals.md` — one row per goal in `<actor> wants to <do X> so that <reason>` form, with priority and in/out-of-scope flag

## Verify

- Every actor in `actors.md` has at least one in-scope goal in `goals.md`.
- Every in-scope goal cites a confirmed actor.
- The out-of-scope section in `goals.md` is non-empty (forces explicit boundary).
- **Cross-stage check (forward):** the human-confirmed actor list will be carried forward verbatim into `01_usecase/output/usecase.md` §Actors.

## Gate

Default human approval — but the gate is *expected* to take multiple
turns to reach. The stage is complete when the human says the
artefacts match their intent.

## Next stage

→ [`../01_usecase/CONTEXT.md`](../01_usecase/CONTEXT.md) — Use case (Fully Dressed)

To advance, the human says: **"Proceed to Stage 01."** The agent then opens the next `CONTEXT.md`, loads only the files in its `Inputs` table, and runs that stage.
