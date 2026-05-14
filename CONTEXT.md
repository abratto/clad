# CONTEXT.md — Workspace router (ICM Layer 1)

You are at the **root** of the CLAD starter workspace. This file tells
agents (and humans) what lives where and which entry point to use for a
given task.

## Where to start by task

| If you want to… | Open |
|---|---|
| Understand the repo and its parts | [`README.md`](README.md) |
| Operate as an AI coding agent | [`AGENTS.md`](AGENTS.md) |
| Learn the methodology | [`methodology/README.md`](methodology/README.md) |
| See a worked example end-to-end | [`features/UC-00-login/README.md`](features/UC-00-login/README.md) (start at `stages/00_actor-goal/`) |
| Start a new feature | **Step 0 — detect state:** if Stage 00 outputs do not exist yet, run Stage 00 first at [`features/_system/stages/00_actor-goal/CONTEXT.md`](features/_system/stages/00_actor-goal/CONTEXT.md) to produce `actors.md` + `goals.md`. If Stage 00 outputs already exist, planning is optional: open [`methodology/overlays/PLANNING.md`](methodology/overlays/PLANNING.md) to sequence in `plan-board.md`, or select an existing approved goal directly. **Step 1 — create UC folders:** when starting a chosen goal, copy [`templates/feature-skeleton/`](templates/feature-skeleton/) to `features/UC-XX-<slug>/`, then open `stages/01_usecase/CONTEXT.md`. |
| Ask "What's next?" / "Where did we leave off?" | Open [`methodology/overlays/TRACKING.md`](methodology/overlays/TRACKING.md), then read `ROADMAP.md` (if present) and the active `features/UC-XX-<slug>/RESUME.md` to propose one concrete next action. |
| Ask "Let's work on a new feature" | Open [`methodology/overlays/PLANNING.md`](methodology/overlays/PLANNING.md), detect project state, and follow conditional routing: Stage 00 first if no actor/goals yet; otherwise optional sequencing via `plan-board.md` or direct goal selection. |
| Author a new concept / sync / use case / actors / goals / spec | [`templates/`](templates/) |
| See the optional Java reference impl | [`reference-impl/java-micronaut-jena/README.md`](reference-impl/java-micronaut-jena/README.md) |
| Track work across features (optional) | [`methodology/overlays/TRACKING.md`](methodology/overlays/TRACKING.md) |

## The five-layer hierarchy in this workspace

| Layer | Files |
|---|---|
| 0 — identity | `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursor/rules/clad.mdc` |
| 1 — workspace routing | this file (`CONTEXT.md`) |
| 2 — stage contract | `features/UC-XX/stages/NN_*/CONTEXT.md` |
| 3 — reference (stable) | `methodology/`, `templates/`, `features/UC-XX/_config/` |
| 4 — working artefacts (per-run) | `features/UC-XX/stages/NN_*/output/` |

Always: load Layers 0–2. Load Layer 3 only as the stage `Inputs` says.
Layer 4 is what you produce or consume.

## Shared resources

| Path | What it is |
|---|---|
| `methodology/` | Stable rules, principles, architecture |
| `templates/` | File templates for concepts, syncs, use cases, flows, stage contracts |
| `reference-impl/` | Optional language-specific reference implementations |
