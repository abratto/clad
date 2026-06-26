# Claude — agent guide

This file is a thin adapter. The canonical instructions live in
[AGENTS.md](AGENTS.md). Read AGENTS.md in full before performing any action
in this repository.

In particular, before editing or generating any file:

1. Open [`AGENTS.md`](AGENTS.md) and read sections 1–5.
2. Open the workspace router: [`CONTEXT.md`](CONTEXT.md).
3. Open the stage contract for the feature you are working on:
   `features/UC-XX/stages/NN_*/CONTEXT.md`.
4. Load only the files that the stage's `Inputs` table names. If the
   table lists a `Skill:` entry, load that skill from `skills/` first —
   its SKILL.md body names the specific `methodology/` and `templates/`
   files to load next.
5. Write to that stage's `output/` folder and stop at the review gate.

Operating outside this loop violates the methodology that the repository
exists to demonstrate.
