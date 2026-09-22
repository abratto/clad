# Stage 01 — Use case

## Why this stage exists

The use case is the **contract every later artefact compiles against**.
Stages 01a, 01b, 02, 03, 04c and 05 each carry a back-cite to a
scenario in this file. If the Postcondition rigour is skipped here
(especially the *no state is modified* assertion on negative paths),
Stage 04c cannot mechanically check the no-enumeration property and
Stage 05 cannot decide whether an observed runtime trace was correct
or merely plausible. Hence: Fully Dressed, both Postcondition
sub-sections, mandatory.

**Feeds:**

- `usecase.md` → 01a (scenarios drive coverage), 01b (one chain table per scenario), 02 (each concept's operational principle must reference these scenarios), 03 (every sync's `Cites` names a scenario), 04c (one flow test per scenario), 05 (verifier walks each scenario's token tree).

**Agent stance for this stage:** you are writing the source of truth
for everything downstream. Prefer over-specifying postconditions to
under-specifying them.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../../_system/stages/00_actor-goal/output/actors.md` | 4 | Confirmed actors |
| `../../../_system/stages/00_actor-goal/output/goals.md` | 4 | Confirmed goals |
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
into Stage 01b. If a failure branch shares the same trigger and user
goal, keep it as an extension under that top-level scenario rather than
creating a second top-level scenario with a success-only name.

A Mermaid `sequenceDiagram` interaction sketch is **optional** — a derived,
human-facing view of the scenario. The canonical, machine-checked diagram is
the Stage 01b chain's `stateDiagram-v2`.

If present, the diagram must stay actor/system-only and must not
introduce concept discovery, sync design, provenance, or state claims
that are not already stated in the prose scenario.

The use case **must be Fully Dressed** before exiting this stage —
the completeness checkbox at the top of `usecase.md` selects "Fully
Dressed", and every scenario carries both `Postconditions — Success`
and `Postconditions — Failure`. See
[`../../../../templates/usecase.md`](../../../../templates/usecase.md)
for level definitions and the rationale.


## Progress checklist

- [ ] Operational principle drafted
- [ ] Actors identified
- [ ] All in-scope goals mapped to scenarios with triggers and postconditions
- [ ] Self-audit: `./clad verify` passes
## Outputs

- `output/usecase.md` — the use case spec (Fully Dressed)

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "usecase.md"
```

- **verify_file_manifest.py:** `output/` contains exactly `usecase.md`.
- **Goal → scenario → chain → sync coverage** is checked at Stage 03
  (`verify_scenario_coverage.py`); at Stage 01 the chain and syncs do not
  exist yet, so it is not run here.

### Semantic checks (human)

- The completeness level is **Fully Dressed**.
- Every scenario has pre-conditions, a main flow, ≥1 observable outcome,
  **and** both `Postconditions — Success` and `Postconditions — Failure`
  sub-sections (the Failure section may say "no state is modified" but
  must be present).
- The optional `sequenceDiagram` interaction sketch, when present, is
  consistent with the prose scenario and remains explanatory only; it
  introduces no concept names, sync names, or extra steps absent from the
  prose.
- `Trigger` is present unless the scenario is a straightforward
  actor-initiated flow.
- Out-of-scope section is non-empty.
- The operational principle reads as a coherent story, not a feature list.
- **Cross-stage check (back):** every in-scope goal in
  `features/_system/stages/00_actor-goal/output/goals.md` corresponds to at least one named
  scenario in `usecase.md`.
- Scenario names are not misleadingly happy-path-only when the scenario
  also contains failure extensions that will be carried into the same
  Stage 01b chain file.

## Gate

Auto-advances (next human gate: Stage 01b). The agent runs the Verify items as a
self-audit and proceeds. If any item fails, the agent stops and
surfaces the defect — it does not silently advance.

## Next stage

→ [`../01a_responsibility-map/CONTEXT.md`](../01a_responsibility-map/CONTEXT.md) — Responsibility map

The agent proceeds to Stage 01a without a human gate.
