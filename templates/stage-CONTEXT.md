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

- <check>
- <check>
