# templates/feature-skeleton/

The empty CLAD feature skeleton. **Copy this folder** to start a new
feature; do not copy `features/UC-00-login/` (which contains worked
example content).

## How to bootstrap a new feature

```sh
cp -R templates/feature-skeleton features/UC-XX-<slug>
# edit features/UC-XX-<slug>/README.md and _config/voice.md
# open features/UC-XX-<slug>/stages/00_actor-goal/CONTEXT.md and start there
```

`UC-XX` should be the next free number; `<slug>` is a short hyphenated
name (e.g. `comment-thread`, not `Comment Thread Feature`).

## What is in here

- `_config/voice.md` — placeholder explaining feature-scoped Layer-3 reference material
- `stages/` — empty stage tree (`00_actor-goal`, `01_usecase`, `02_concepts`,
  `03_syncs`, `04_implement` with sub-stages `04a..04e`, `05_verify`),
  each with a `CONTEXT.md` and an empty `output/`

## What is **not** in here

- No example artefacts. Do not copy `features/UC-00-login/output/*` into a
  new feature; derive your own from the actor/goal stage.
- No `README.md` for the new feature. Write one yourself.
