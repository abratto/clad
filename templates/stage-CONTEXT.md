<!-- Stage CONTEXT.md template. Purpose: see methodology/implementation/STAGES.md and the ICM five-layer hierarchy in AGENTS.md §4. -->

# Stage <NN> — <name>

> Stage `CONTEXT.md` template. This is the contract for what the agent
> does in this stage.

## Inputs

> Layer 4 (working) inputs are the previous stage's `output/`.
> Layer 3 (reference) inputs are stable methodology files. List
> exactly the files the agent must load — no more, no less.

| Path | Layer | Why |
|---|---|---|
| `../<previous-stage>/output/` | 4 | Working artefacts from prior stage |
| `../../../../methodology/<...>` | 3 | Reference material |
| `../../_config/<...>` | 3 | Feature-scoped reference |

## Process

> One short paragraph saying what the agent does. Not a recipe — a
> description. The recipe is in the referenced methodology files.

## Outputs

> Closed list. The agent must not write files outside this list.

- `output/<filename>` — <what it contains>
- `output/<filename>` — <what it contains>

## Verify

> How the next stage (or the human) will check this stage's work.
> Include at least one **cross-stage consistency check** (e.g. "every
> actor in `00_actor-goal/output/actors.md` whose goal is in-scope
> appears in at least one concept's operational principle"). See
> `methodology/implementation/STAGES.md` §"Cross-stage consistency".

- <check>
- <check (cross-stage)>

## Gate

> The standard gate is: the human reviews `output/`, edits if
> necessary, and either says "go" (move to next stage) or sends the
> agent back. Note any stage-specific gate semantics here (e.g. Stage
> 00's collaboration loop may take multiple turns before this gate is
> reached).

- Default: human approval of `output/` contents.
- Stage-specific: <e.g. "agent must not have produced files outside the Outputs list">.
