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
| Skill: `clad-usecase-authoring` | 3 | Use case authoring reference (see skills/ directory) |
| `../../../../methodology/core/CLAD.md` | 3 | Methodology |
| `../../../../templates/usecase.md` | 3 | Output template |
| `../../_config/voice.md` | 3 | Feature voice |

## Process

Draft `usecase.md` by composing one operational principle paragraph
that covers all in-scope goals from stage 00. List the actors verbatim
from `actors.md`. Write one named scenario per in-scope goal (or per
distinct trigger if a goal has several). Write the out-of-scope
section by lifting out-of-scope goals from `goals.md` and adding any
implicit exclusions.

Use scenario names that can carry both the main flow and its extensions
into Stage 02b. If a failure branch shares the same trigger and user
goal, keep it as an extension under that top-level scenario rather than
creating a second top-level scenario with a success-only name.

Check `../../clad.properties` for `stages.usecase.require-sequence-diagram`.
If set to `true` (the default): **a Mermaid `sequenceDiagram` is
required** inside each scenario as a derived, human-facing interaction
sketch. If set to `false`, the diagram is optional.

If present, the diagram must stay actor/system-only and must not
introduce concept discovery, sync design, provenance, or state claims
that are not already stated in the prose scenario.

The use case **must be Fully Dressed** before exiting this stage —
the completeness checkbox at the top of `usecase.md` selects "Fully
Dressed", and every scenario carries both `Postconditions — Success`
and `Postconditions — Failure`. See
[`../../../../templates/usecase.md`](../../../../templates/usecase.md)
for level definitions and the rationale.

## Outputs

- `output/usecase.md` — the use case spec (Fully Dressed)

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "usecase.md"
python3 ../../../../quality-gate/verify_scenario_coverage.py \
  --goals ../00_actor-goal/output/goals.md \
  --usecase output/usecase.md \
  --chain-dir ../02b_chain-table/output \
  --sync-dir ../03_syncs/output
```

- **verify_file_manifest.py:** `output/` contains exactly `usecase.md`.
- **verify_scenario_coverage.py:** every in-scope goal maps to a
  scenario heading; chain file and sync citation warnings are expected
  at this stage and do not block the gate.

### Semantic checks (human)

- The completeness level is **Fully Dressed**.
- Every scenario has pre-conditions, a main flow, ≥1 observable outcome,
  **and** both `Postconditions — Success` and `Postconditions — Failure`
  sub-sections (the Failure section may say "no state is modified" but
  must be present).
- **If `stages.usecase.require-sequence-diagram=true`:** every scenario
  has a Mermaid `sequenceDiagram` interaction sketch.
- The diagram is consistent with the prose scenario and remains
  explanatory only; it introduces no concept names, sync names, or
  extra steps absent from the prose.
- `Trigger` is present unless the scenario is a straightforward
  actor-initiated flow.
- Out-of-scope section is non-empty.
- The operational principle reads as a coherent story, not a feature list.
- **Cross-stage check (back):** every in-scope goal in
  `00_actor-goal/output/goals.md` corresponds to at least one named
  scenario in `usecase.md`.
- Scenario names are not misleadingly happy-path-only when the scenario
  also contains failure extensions that will be carried into the same
  Stage 02b chain file.

## Gate

Auto-advances (next human gate: Stage 02b). The agent runs the Verify items as a
self-audit and proceeds. If any item fails, the agent stops and
surfaces the defect — it does not silently advance.

## Next stage

→ [`../02a_responsibility-map/CONTEXT.md`](../02a_responsibility-map/CONTEXT.md) — Responsibility map

The agent proceeds to Stage 02a without a human gate.
