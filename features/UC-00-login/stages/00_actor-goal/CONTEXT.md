# Stage 00 — Actor / Goal (UC-00-login)

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
