# Stage 01 — Use case

## Why this stage exists

The use case is the **contract every later artefact compiles against**.
Stages 02a, 02b, 02, 03, 04c and 05 each carry a back-cite to a
scenario in this file. If the Postcondition rigour is skipped here
(especially the *no state is modified* assertion on negative paths),
Stage 04c cannot mechanically check the no-enumeration property and
Stage 05 cannot decide whether an observed runtime trace was correct
or merely plausible. Hence: Fully Dressed, both Postcondition
sub-sections, mandatory.

**Feeds:**

- `usecase.md` → 02a (scenarios drive coverage), 02b (one chain table per scenario), 02 (each concept's operational principle must reference these scenarios), 03 (every sync's `Cites` names a scenario), 04c (one flow test per scenario), 05 (verifier walks each scenario's token tree).

**Agent stance for this stage:** you are writing the source of truth
for everything downstream. Prefer over-specifying postconditions to
under-specifying them.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../00_actor-goal/output/actors.md` | 4 | Confirmed actors |
| `../00_actor-goal/output/goals.md` | 4 | Confirmed goals |
| `../../../../methodology/core/CLAD.md` | 3 | Methodology |
| `../../../../templates/usecase.md` | 3 | Output template |
| `../../_config/voice.md` | 3 | Feature voice |

## Process

Draft the use case for UC-00-login. Identify actors and the named
scenarios the feature must satisfy. One paragraph for the operational
principle. Each scenario is a trigger + expected outcomes. Be honest
about what is out of scope.

## Outputs

- `output/usecase.md` — the use case spec

## Verify

- Every scenario has a trigger, pre-conditions, and at least one
  observable outcome.
- Out-of-scope section is non-empty.
- The operational principle reads as a coherent story, not a feature
  list.
- **Cross-stage check (back):** every in-scope goal in
  `../00_actor-goal/output/goals.md` corresponds to at least one named
  scenario in `usecase.md`.

## Gate

Default human approval. The use case is the contract every later
stage compiles against; gate carefully.
