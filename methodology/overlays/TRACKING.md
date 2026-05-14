# Workflow overlay — TRACKING

> **Status: optional.** Nothing in `methodology/core/`,
> `methodology/architecture/`, or `methodology/implementation/`
> requires this. Use it if you want lightweight progress hygiene
> across sessions; ignore it if your workflow already provides one.

## Why an overlay

CLAD's stage gates already give you decision points. They do not
tell you *which feature you are on this week*, *what your phase
plan looks like*, or *where you stopped last session*. Some teams
(and some agents) need that scaffolding; others find it noise.
Hence: overlay, not core.

## The four conventions

### 1. One active feature at a time

Open exactly one `features/UC-XX/` at any moment. If you must
switch, finish the current stage's gate and write a one-line
**resume point** at the top of that stage's `output/` (e.g. as a
top-level comment in the most recent file you touched).

### 2. Suggested issue labels

Match the labels used by `.github/ISSUE_TEMPLATE/`:

- `clad:in-progress` — currently active feature/issue
- `clad:done` — gate passed, merged
- `clad:spec-needed` — flagged for an iterative-change spec before
  any code

### 3. Roadmap convention

The repo ships [`ROADMAP.md`](../../ROADMAP.md) as a working example.
Conventions:

- **At most one phase row has status `doing`** at any time. The other
  rows are `done`, `next`, or `later`. The `doing` row points at the
  active `features/UC-XX/` folder.
- A **`## Resume point`** section with a `**Last updated:** YYYY-MM-DD`
  line records where the last session stopped.

CI enforces both via
[`.github/scripts/check-roadmap-hygiene.sh`](../../.github/scripts/check-roadmap-hygiene.sh)
(threshold for the resume point is 60 days; override with the
`ROADMAP_MAX_AGE_DAYS` env var if you need to). The check is a no-op
if `ROADMAP.md` is absent — opt out by deleting the file.

A starter template lives at [`../../templates/roadmap.md`](../../templates/roadmap.md).

### 4. Session start / resume checklist

At the top of a new session:

1. Read [`../../AGENTS.md`](../../AGENTS.md) §1–5 (or its adapter file for your agent).
2. Read [`../../CONTEXT.md`](../../CONTEXT.md) (the workspace router).
3. Identify the active feature (label `clad:in-progress` or `ROADMAP.md` `doing`).
4. Read that feature's `README.md` and the **next** stage's `CONTEXT.md`.
5. Look for a resume-point comment in the most recent `output/` file.
6. Proceed.

## Natural-language intake shortcuts (for LLM sessions)

This overlay supports simple human prompts so users do not need to
remember multiple command styles.

### "What's next?"

Agent behavior:

1. Read `ROADMAP.md` (if present) and identify the `doing` row.
2. Read the active feature's `RESUME.md`.
3. Identify the first stage whose gate is not yet approved.
4. Reply with one concrete next action (single step), then wait for
  human confirmation.

### "Let's work on a new feature"

Agent behavior:

1. Open [`PLANNING.md`](PLANNING.md) and detect project state.
2. If Stage 00 outputs do not exist, route to system-scope Stage 00 at
  `features/_system/stages/00_actor-goal/CONTEXT.md`.
3. If Stage 00 outputs exist, planning is optional: sequence in
  `plan-board.md` or choose an existing approved goal directly.
4. If goals changed after planning, run the plan-drift check and update
  `plan-board.md` before starting new work.
5. Ask one targeted planning question only when sequencing is unclear.

### "Resume work"

Agent behavior:

1. Read `AGENTS.md`, `CONTEXT.md`, `ROADMAP.md` (if present), and the
  active `RESUME.md`.
2. State current feature, current stage, and next task out loud.
3. Wait for explicit confirmation before editing files.

## What this overlay does **not** do

- It does not change the stage map.
- It does not relax any of the hard rules in
  [`../implementation/RULES.md`](../implementation/RULES.md).
- It does not introduce new artefacts that other stages depend on.

If you find yourself wanting to fold any of this into the core,
**don't** — surface the request and discuss first. Keeping the
core small is what keeps the methodology portable.
