# Stage 00 — Actor / Goal (system scope)

> **Scope: run once per project brief, not once per feature.**
> This `CONTEXT.md` is for the *system-level* pass of Stage 00 — the
> pass that produces `actors.md` and `goals.md` for the whole system.
> Each in-scope goal will later become one UC folder (Stage 01 onwards).
> Do **not** use this file inside a `features/UC-XX-<slug>/` folder.

## Why this stage exists

This stage answers *"who wants what."* Without it, every later stage
is solving for an unstated user, and the use case drifts. The human's
brief alone is too soft to plan against; turning it into a confirmed
actor list and goal list is what lets the rest of the loop be
mechanical.

**Feeds:**

- `actors.md` → Stage 01 in each UC folder (verbatim actor list in
  `usecase.md`); Stage 02a (every in-scope actor must be represented
  by ≥1 concept).
- `goals.md` → one `features/UC-XX-<slug>/` folder per in-scope goal,
  created **after** this gate is passed. Out-of-scope goals lift into
  each use case's *Out of scope* section.
- `port-spec.md` (optional) → Stage 04b and Stage 04c when an external
  adapter contract exists; Delivery uses it to require a contract test
  tier in CI.

**Agent stance for this stage:** propose, ask ≤5 questions, iterate.
Do not write `actors.md` / `goals.md` until the human signals
agreement. Do not create any UC folder during this stage.

## Inputs

| Path | Layer | Why |
|---|---|---|
| (the human's brief) | — | Source of intent |
| Skill: `clad-system-scoping` | 3 | System scoping reference (see skills/ directory) |
| `../../../templates/actors.md` | 3 | Output template |
| `../../../templates/goals.md` | 3 | Output template |
| `../../../templates/port-spec.md` | 3 | Optional output template when an external adapter contract exists |
| `../../../methodology/implementation/STAGES.md` | 3 | §"Scope: system-level vs per-UC" and §"Stage 00 — `00_actor-goal/`" — collaboration semantics |

## Process

**This stage is multi-turn and collaborative.** The agent:

1. **Proposes** an initial actor/goal list inferred from the human's brief.
2. **Asks at most 5 clarifying questions** in a single turn.
3. Asks whether an existing API contract, published spec, or external
  test suite constrains the system's adapter surface.
4. If yes, obtains the contract source, records adapter compliance as a
  system-level constraint in `goals.md`, and prepares `port-spec.md`
  from the template. If no, records that the adapter format is a design
  choice for Stage 04b and omits `port-spec.md`.
5. Iterates with the human until they signal agreement.
6. **Only then** writes `actors.md`, `goals.md`, and optional
  `port-spec.md` per the templates.

The agent does not invent goals the human has not confirmed. If the
brief is too thin to propose anything, the agent asks for more context
before drafting.

## Outputs

- `output/actors.md` — one row per actor (name, role, primary concerns)
- `output/goals.md` — one row per goal with a short `Goal` phrase, a
  separate `Rationale`, plus priority and in/out-of-scope flag
- `output/port-spec.md` — optional, only when an external adapter
  contract exists

## Verify

- Every actor in `actors.md` has at least one in-scope goal in `goals.md`.
- Every in-scope goal cites a confirmed actor.
- The out-of-scope section in `goals.md` is non-empty (forces explicit boundary).
- If an external adapter contract exists, `port-spec.md` names its source,
  fixed conventions, and contract test suite (if any).
- If no external adapter contract exists, `goals.md` says the adapter
  format is a Stage 04b design choice and `port-spec.md` is absent.
- **Forward-check:** count the in-scope goals. That many UC folders
  will be created next; if the count seems too high or too low, surface
  that to the human before the gate closes.

## Gate

**Gate 0 (system-level).** Before asking for approval, list every output
file produced (`actors.md`, `goals.md`, and optional `port-spec.md`) with
a one-line summary. Then ask for human approval.

Default human approval — but the gate is *expected* to take multiple
turns to reach. The stage is complete when the human says the
artefacts match their intent.

## Next stage

After the gate passes:

1. For each in-scope goal in `output/goals.md`, copy
   `templates/feature-skeleton/` to a new `features/UC-XX-<slug>/`
   folder (assign UC numbers in sequence starting from 01).
2. Open `features/UC-01-<slug>/stages/01_usecase/CONTEXT.md` and run
   Stage 01 for the first UC, carrying `actors.md` and `goals.md` as
   inputs.
3. Repeat Stage 01 for each remaining UC folder in order.

The human initiates this by saying: **"Proceed — create the UC
folders."**
