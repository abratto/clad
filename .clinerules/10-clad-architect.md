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

- Identify the current stage from either the system-level Stage 00 folder
	under `features/_system/stages/00_actor-goal/` or a per-UC folder under
	`features/UC-XX-<slug>/stages/`.
- Read prior stage outputs in chronological order.
- Read `features/UC-XX-<slug>/RESUME.md` before writing when you are inside
	a per-UC feature. Stage 00 system work under `features/_system/` does not
	use a per-feature `RESUME.md` yet.
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
- For Stage `03`, build a Sync Contract Matrix first: source row, target row, exact `when`, exact `then`, allowed literals.
- For Stage `03`, preserve literal identity exactly: numeric status codes are numeric, and string/status literals keep exact casing and hyphenation.
- For Stage `03`, do not invent convenience payload fields; use only approved constants or fields explicitly emitted by prior outcomes.
- For Stage `03`, if a 02b row and 02 concept signature disagree, stop and reopen Stage `02` instead of reconciling them yourself.
- For Stage `03a`, copy sync names, action names, field names, pattern labels, keys, and literals exactly from the approved Stage `03` files.
- For Stage `03a`, treat any token mismatch as a defect to surface, not something to normalize in the dependency review output.
- For Stage `05`, trace runtime behavior back to use-case scenarios using flow tokens.

## Working memory

- Treat `features/UC-XX-<slug>/RESUME.md` as live working memory during
	per-UC work. For system-level Stage 00, rely on the current stage output
	plus the human-approved brief until UC folders exist.
- At the end of each turn, update `RESUME.md` with blocker, failing command, files touched, and next concrete steps.
- Keep summaries short; reference headings and file paths instead of restating long documents.

## Approval boundary

Keep this rule enabled until the human explicitly approves moving into Stage `04`. Then disable this rule and enable the red rule.
