# Stage 02a — Responsibility map

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
| `../01_usecase/output/usecase.md` | 4 | Scenarios to cover |
| `../00_actor-goal/output/actors.md` | 4 | For cross-stage check |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | What counts as a concept |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rule R1 |
| `../../../../templates/responsibility-map.md` | 3 | Output template |

## Process

Identify the concepts the feature requires (one user-facing capability
each). Produce a single flat table with one row per concept: name,
owned state (one line), owned actions (names only). Do **not** draft
full concept specs here — that is Stage 02. Do **not** describe how
concepts coordinate — that is Stage 02b.

The reason for splitting this out is to give the human a clean review
surface: *"these are the right concepts and they own the right
things"* — before any choreography or coordination is committed to
paper.

## Outputs

- `output/responsibility-map.md` — the table

## Verify

- Every concept's `Owned state` is one line; if it needs more, the
  concept is doing too much (split it).
- Every concept's `Owned actions` is a comma-separated list of names
  only — no signatures, no outcomes (those are Stage 02).
- **Cross-stage check (back):** every actor in
  `../00_actor-goal/output/actors.md` whose goal is in-scope is
  represented by at least one concept (typically as the actor of that
  concept's first action).
- **Coverage:** every scenario in `../01_usecase/output/usecase.md`
  has at least one concept listed under it in the *Coverage check*
  section; every concept appears in at least one scenario.

## Gate

Default human approval. **Do you agree with this step? Any
corrections before I continue?**
