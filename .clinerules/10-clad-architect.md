# CLAD Architect Rule

Use this rule only while working Stages `00`-`03` or `05`.

## Mission

Produce or review pre-implementation artefacts only: actor/goal lists, use cases, responsibility maps, chain tables, concept specs, syncs, dependency reviews, and verification traces.

Do not write implementation code or tests.

## Read order

Before writing anything:
1. Read `AGENTS.md`.
2. Read `methodology/implementation/STAGES.md`.
3. Read the current stage `CONTEXT.md`.
4. Load only the files listed in that stage's `Inputs` table.

## Stage discipline

- Identify the current stage from the feature folder under `features/UC-XX-<slug>/stages/`.
- Read prior stage outputs in chronological order.
- Read `features/UC-XX-<slug>/RESUME.md` before writing.
- State the current stage, last completed stage, and artefact being produced.
- Produce the current stage outputs only, then stop at the gate.
- Wait for explicit human approval before advancing.

## Hard constraints

- One stage, one job.
- Write only to the current stage's closed `Outputs` list.
- No implementation artefacts. No Java implementation files. No test files.
- For Stage `02b`, every named scenario has exactly one canonical chain file; the first row is `Web.handle`, the last row is `Web.respond`.
- For Stage `03`, write one sync per chain-table transition; do not collapse transitions.
- For Stage `03`, syncs are declarative only: `when X -> then Y`, no imperative branching.
- For Stage `05`, trace runtime behavior back to use-case scenarios using flow tokens.

## Working memory

- Treat `features/UC-XX-<slug>/RESUME.md` as live working memory.
- At the end of each turn, update `RESUME.md` with blocker, failing command, files touched, and next concrete steps.
- Keep summaries short; reference headings and file paths instead of restating long documents.

## Approval boundary

Keep this rule enabled until the human explicitly approves moving into Stage `04`. Then disable this rule and enable the red rule.
