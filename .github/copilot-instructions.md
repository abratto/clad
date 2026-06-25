# GitHub Copilot — repository instructions

This file is a thin adapter. The canonical instructions live in
[`../AGENTS.md`](../AGENTS.md). Read AGENTS.md in full before performing
any action in this repository.

When suggesting code or edits in this repository:

1. Treat [`../AGENTS.md`](../AGENTS.md) sections 1–5 as binding.
2. Identify which **feature** (`features/UC-XX/`) and which **stage**
   (`stages/NN_*/`) the user is working in. Open that stage's
   `CONTEXT.md` before suggesting anything.
3. Load only the files that the stage's `Inputs` table names. When a
   `Skill:` entry is present, load that skill from `skills/` first.
4. Honour the hard rules in `AGENTS.md` §5 — especially "no concept
   imports another concept" and "syncs are declarative."
5. Write outputs only into the stage's `output/` folder.

If a request would require violating a hard rule, surface the conflict
to the user instead of silently relaxing the rule.
