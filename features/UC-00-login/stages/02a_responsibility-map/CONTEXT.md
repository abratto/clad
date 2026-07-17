# Stage 02a — Responsibility map (UC-00-login)

## Why this stage exists

A clean human-review surface for *"are these the right concepts and do
they own the right things?"* — **before** any choreography or anatomy
is committed to paper. Without 02a the human reviews concept fan-out
(02b) and concept anatomy (02) at the same time, which doubles the
rework cost when a concept turns out to be wrong.

**Feeds:**

- `responsibility-map.md` → 02b (only listed concepts and actions may appear in chains), 02 (one `*.concept.md` is produced per row), 03a (one dependency-review card per concept).

**Agent stance for this stage:** resist the urge to draft full
signatures or coordination here. Names and one-line state only.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | UC-00-login scenarios |
| `../00_actor-goal/output/actors.md` | 4 | Cross-stage check |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | What counts as a concept |
| `../../../../methodology/implementation/RULES.md` | 3 | R1 |
| Skill: `clad-responsibility-mapping` | 3 | Responsibility mapping reference |
| `../../../../templates/responsibility-map.md` | 3 | Output template |

## Process

Identify the concepts UC-00-login requires. Produce one row per
concept in `output/responsibility-map.md`. Do **not** draft full
specs (Stage 02) and do **not** describe choreography (Stage 02b).

## Outputs

- `output/responsibility-map.md`

## Verify

### Automated checks

```
python3 ../../../../quality-gate/verify_file_manifest.py --dir output --expected "responsibility-map.md"
```

- **verify_file_manifest.py:** `output/` contains exactly the expected files.

### Semantic checks (human)

- One row per concept; one-line state; action names only.
- Every UC-00 actor with an in-scope goal is represented.
- Every UC-00 scenario lists at least one concept; every concept
  appears in at least one scenario.

## Gate

Auto-advances (next human gate: Stage 02b). The `verify_file_manifest.py`
script must pass before advancing.

## Next stage

→ [`../02b_chain-table/CONTEXT.md`](../02b_chain-table/CONTEXT.md) — Chain tables (one per scenario)

The agent proceeds to Stage 02b without a human gate.
