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
>
> **Mandatory self-audit.** Before requesting the human gate, the
> agent must run every item in this section as a pass/fail checklist.
> If any item fails, the stage is not complete: do not present it as
> ready for approval. Stop, name the earliest invalid upstream stage or
> local defect, and ask to reopen or repair that stage instead of
> normalizing the mismatch downstream.

- <check>
- <check (cross-stage)>

## Gate

> The standard gate is: the human reviews `output/`, edits if
> necessary, and either says "go" (move to next stage) or sends the
> agent back. Note any stage-specific gate semantics here (e.g. Stage
> 00's collaboration loop may take multiple turns before this gate is
> reached).
>
> **Standard gate phrasing.** When you reach the gate, end your turn
> with this exact line (no embellishment, no apology, no preamble):
>
> > **Do you agree with this step? Any corrections before I continue?**
>
> "Ready for review" means the stage passed its `Verify` self-audit and
> is being presented to the human. "Gate passed" means the human has
> explicitly approved it. Do not treat these as the same state.
>
> Use this phrasing in every stage's `Gate` section so the human sees
> a consistent stop signal across stages. The rejection protocol in
> [`../AGENTS.md`](../AGENTS.md) §6 takes over from here.

- Default: human approval of `output/` contents.
- Stage-specific: <e.g. "agent must not have produced files outside the Outputs list">.

## Advancing

> Do not open the next stage's `CONTEXT.md` yourself. After this stage's
> `output/` is written, end your turn by running the gate-driven advance
> command, which runs this stage's checks, enforces stage ordering, and
> tells you the next step:
>
> ```
> python3 quality-gate/advance.py --feature features/UC-XX-<slug>
> ```
>
> Treat its output as your next instruction. It advances you, stops you
> at a human gate, or returns you to this stage with the defects to fix.
> See AGENTS.md §2 principle 12 and
> `methodology/implementation/STAGES.md` §"Gate-driven advance".
