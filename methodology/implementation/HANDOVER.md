# HANDOVER.md — self-orienting prompt for any model

Use this file when you want a fresh model session to pick up one
feature mid-flight without manual stage narration.

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

Then locate the current stage by inspecting `features/{{UC-XX-slug}}/stages/` in chronological order. The current stage is the first stage directory that has no `output/` files, or has an `output/` directory with no artefacts.

Then read all prior stages' `output/` artefacts in chronological order to build full context.

Then read `features/{{UC-XX-slug}}/RESUME.md` for fine-grained state (corrections, rejections, deferred concepts) that is not visible from folder structure alone.

Before any edits or stage work, state out loud:
- which feature you are working on,
- which stage you diagnosed as current,
- what the next task is.

Then wait for explicit human confirmation before doing anything else.

Standing rules you must follow:
- Gate behaviour: stop after every stage output is produced and wait for explicit human approval before proceeding.
- Commit cadence: one commit per gate approval on the feature branch, message format `feat(UC-XX): Stage NN — <artefact name>`.
- Branch name: `feat/UC-XX-<slug>`.
- Never write artefacts directly to `main`.
- After each gate approval, overwrite `features/{{UC-XX-slug}}/RESUME.md` before committing.
```
