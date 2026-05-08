# `features/_system/` — system-level Stage 00

This folder is the canonical home for **Stage 00 (Actor / Goal)** when
it is run at **system scope** — that is, for a fresh project brief that
has not yet been decomposed into individual UC folders.

## Why this folder exists

Stage 00 produces `actors.md` and `goals.md`. For a real system with
more than one goal, those artefacts describe the *whole system*, not a
single feature. Creating a `features/UC-XX-<slug>/` folder before
Stage 00 is complete is structurally wrong: the UC folders are created
**after** the goal list is confirmed, one folder per in-scope goal.

`_system/` gives Stage 00 a home that is clearly outside any UC scope.

## What lives here

```
features/_system/
├── README.md                    ← this file
└── stages/
    └── 00_actor-goal/
        ├── CONTEXT.md           ← Stage 00 contract (system scope)
        └── output/
            ├── actors.md        ← written after human approval
            └── goals.md         ← written after human approval
```

## Relationship to UC folders

Once `actors.md` and `goals.md` are approved:

1. Read every in-scope goal in `goals.md`.
2. Create one `features/UC-XX-<slug>/` folder per in-scope goal by
   copying `templates/feature-skeleton/`.
3. Run Stage 01 inside each new UC folder, carrying `actors.md` and
   `goals.md` forward as inputs.

## What does NOT live here

Everything from Stage 01 onwards lives inside a per-UC folder. This
folder never grows beyond Stage 00 output.

## Cross-reference

- Stage 00 contract: [`stages/00_actor-goal/CONTEXT.md`](stages/00_actor-goal/CONTEXT.md)
- Stage scope rules: [`../../methodology/implementation/STAGES.md`](../../methodology/implementation/STAGES.md) §"Scope: system-level vs per-UC"
- Template for new UC folders: [`../../templates/feature-skeleton/`](../../templates/feature-skeleton/)
- Worked single-goal example: [`../UC-00-login/`](../UC-00-login/) *(edge case — read the note there)*
