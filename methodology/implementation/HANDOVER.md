# HANDOVER.md — self-orienting prompt for any model

Use this file when you want a fresh model session to pick up one
feature mid-flight without manual stage narration.

This file is the **mechanical handoff payload** for the
`workflow.session-per-stage=true` mode in
[`STAGES.md`](STAGES.md). Under that mode, `advance.py` (exit `30`)
substitutes `{{UC-XX-slug}}` and prints the copy/paste block below so the
operator can start a fresh session whose only inputs are the on-disk
artefacts. It doubles as a manual recovery prompt for any session that
needs to re-orient from disk.

On harnesses that support sub-agents, the same block is a ready-made
sub-agent mission: spawn a sub-agent with this block (slug already
substituted) to give it a clean context window for exactly one stage.
This is the **recommended default when orchestration is available** —
one sub-agent per stage, each driving `./clad advance`. The producing
sub-agent ends its turn with `./clad advance`; the parent spawns the
next stage, or, at a human gate, the parent/human approves and the next
sub-agent crosses the gate on entry. See
[`STAGES.md`](STAGES.md) §"Orchestration: one sub-agent per stage" for
the full loop and the no-sub-agent fallback. The gate decision stays
with the parent/human — the sub-agent only produces the stage's
`output/`.

## Human input (only one placeholder)

- Replace `{{UC-XX-slug}}` with the feature folder name
  (example: `UC-01-register`).
- Do not add stage notes unless you want to override repo-derived state.

## Copy/paste prompt

```text
You are taking over feature `{{UC-XX-slug}}` in this repository.

Before doing anything, read these files in this exact order:
1. `AGENTS.md`
2. `methodology/implementation/STAGES.md`
3. `methodology/implementation/DELIVERY.md`
4. `methodology/implementation/HANDOVER.md`
5. `templates/usecase.md`

Then determine the current stage the sanctioned way — run:

```
python3 quality-gate/advance.py --feature features/{{UC-XX-slug}}
```

`advance.py` owns the transition decision (never self-select a stage). Its
output names the current stage, the next stage, or a human gate. If it is
unavailable, you may fall back to inspecting
`features/{{UC-XX-slug}}/stages/` in chronological order, but you must still
run `advance.py` before writing anything.

Then read all prior stages' `output/` artefacts in chronological order to build full context.

Then read `features/{{UC-XX-slug}}/RESUME.md` for fine-grained state (corrections, rejections, deferred concepts) that is not visible from folder structure alone.

Before any edits or stage work, state out loud:
- which feature you are working on,
- which stage you diagnosed as current,
- what the next task is.

Then wait for explicit human confirmation before doing anything else.

Standing rules you must follow:
- Gate behaviour: stages auto-advance between human gates. Stop and wait for explicit human approval only at Gate 1 (after 01b), Gate 2 (after 03b), and Gate 3 (after 04c). `advance.py` owns the transition and prints the gate summary and approval command — do not self-select a stage or write your own approval prompt.
- Commit cadence: one commit per gate approval on the feature branch, message format `feat(UC-XX): Gate N — <label> (stages NN–NN)`.
- Branch name: `feat/UC-XX-<slug>`.
- Never write artefacts directly to `main`.
- After each gate approval, overwrite `features/{{UC-XX-slug}}/RESUME.md` before committing.
- **RESUME.md is machine-owned in part.** Do NOT hand-edit the
  `## Gate snapshot` block (the lines carrying `content hash`). `approve_gate.py`
  writes it; hand-editing or deleting a hash line makes the sequence guard see a
  stale/invalid approval and blocks `advance` (the conduit rebuild hit this once).
  You may edit only the live-memory bullets at the top, and only when the task
  says so — otherwise leave `RESUME.md` to `advance.py`.
```
