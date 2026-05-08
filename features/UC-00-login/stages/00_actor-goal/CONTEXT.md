# Stage 00 — Actor / Goal (UC-00-login)

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
| (the human's brief, in this seed: "log in with username + password to get a session") | — | Source of intent |
| `../../../../templates/actors.md` | 3 | Output template |
| `../../../../templates/goals.md` | 3 | Output template |
| `../../../../methodology/implementation/STAGES.md` | 3 | §"Stage 00" — collaboration semantics |

## Process

> **Seed-time note.** For this worked example, the agent generates
> `actors.md` and `goals.md` directly from the embedded brief without
> iteration; the **collaborative semantics described in
> `STAGES.md` §"Stage 00" apply at feature-authoring time, not at
> seed-generation time.** When you copy `templates/feature-skeleton/`
> for a new feature, follow the multi-turn process there.

For UC-00-login the brief is intentionally minimal: one actor (an end
user with a registered account), one in-scope goal (sign in to obtain a
session), and a small explicit out-of-scope list (registration, reset,
MFA, SSO, logout).

## Outputs

- `output/actors.md`
- `output/goals.md`

## Verify

- Every actor has at least one in-scope goal.
- The out-of-scope section is non-empty.
- **Cross-stage check (forward):** the actor `EndUser` appears verbatim in `01_usecase/output/usecase.md` §Actors (as `User`, the in-feature label).

## Gate

Default — for the seed, the gate is the human PR review.

## Next stage

→ [`../01_usecase/CONTEXT.md`](../01_usecase/CONTEXT.md) — Use case (Fully Dressed)

To advance, the human says: **"Proceed to Stage 01."** The agent then opens the next `CONTEXT.md`, loads only the files in its `Inputs` table, and runs that stage.
