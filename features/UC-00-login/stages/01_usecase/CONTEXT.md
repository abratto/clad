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

Draft the use case for UC-00-login. Identify actors and the named
scenarios the feature must satisfy. One paragraph for the operational
principle. Each scenario is a trigger + expected outcomes. Be honest
about what is out of scope.

An optional Mermaid `sequenceDiagram` may be included inside a scenario
as a human-facing interaction sketch, but it is derived only from the
scenario prose. If present, it must stay actor/system-only and must not
introduce concept names, sync names, provenance, or state claims.

Default expectation: include the diagram when it materially improves
review clarity, especially for scenarios with branching extensions,
opaque error handling, or more than three interaction steps. Omit it
when it would merely restate a short linear scenario without adding
useful visual structure.

## Outputs

- `output/usecase.md` — the use case spec

## Verify

### Automated checks

```
python3 ../../../../quality-gate/verify_file_manifest.py --dir output --expected "usecase.md"
```

- **verify_file_manifest.py:** `output/` contains exactly the expected files.

### Semantic checks (human)

- Every scenario has an explicit trigger. *(The trigger names a user action or external event, not just "user does something".)*
- Every scenario's main flow begins with an action by the primary actor.
- All actors named in scenarios come from `../00_actor-goal/output/actors.md`.
- No scenario lists a domain entity (Loan, Copy, Title, etc.) as an actor.
- Pre-conditions, observable outcomes, and postconditions (Success and Failure) are present in each scenario.
- Any Mermaid `sequenceDiagram` included in the use case matches the
	prose scenario and remains explanatory only.
- Scenarios with branching extensions, opaque failure paths, or longer
	interaction sequences include an interaction sketch unless it would
	add no review value.
- Out-of-scope section is non-empty.
- The operational principle reads as a coherent story, not a feature list.
- **Cross-stage check (back):** every in-scope goal in `../00_actor-goal/output/goals.md` corresponds to at least one named scenario in `usecase.md`.

## Gate

Auto-advances (next human gate: Stage 02b). The `verify_file_manifest.py`
script must pass before advancing.

## Next stage

→ [`../02a_responsibility-map/CONTEXT.md`](../02a_responsibility-map/CONTEXT.md) — Responsibility map

The agent proceeds to Stage 02a without a human gate.
