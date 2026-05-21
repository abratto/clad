# templates/feature-skeleton/

The empty CLAD feature skeleton. **Copy this folder** to start a new
per-UC feature (Stages 01–05); do not copy `features/UC-00-login/`
(which contains worked example content).

> **Stage 00 is system-level.** It lives in
> `features/_system/stages/00_actor-goal/` and is run **once per project
> brief**, not once per UC. This skeleton covers only Stages 01–05 (the
> per-UC work). Never add a `00_actor-goal/` folder inside a UC folder.

## How to bootstrap a new feature

```sh
cp -R templates/feature-skeleton features/UC-XX-<slug>
# replace the starter features/UC-XX-<slug>/README.md with your feature-specific text,
# then edit _config/voice.md,
# and _config/package-and-layout.md
# open features/UC-XX-<slug>/stages/01_usecase/CONTEXT.md and start there
```

`UC-XX` should be the next free number; `<slug>` is a short hyphenated
name (e.g. `comment-thread`, not `Comment Thread Feature`).

Run Stage 00 (`features/_system/stages/00_actor-goal/`) to completion
**before** copying this skeleton for any UC.

## What is in here

- `_config/voice.md` — placeholder explaining feature-scoped Layer-3 reference material
- `_config/package-and-layout.md` — canonical package/source-root settings
- `stages/` — empty stage tree (`01_usecase`, `02a_responsibility-map`,
  `02b_chain-table`, `02_concepts`, `03_syncs`, `03a_dependency-review`,
  `04_implement` with sub-stages `04a..04e`, where `04d` and `04e`
  each contain structural red/green child folders, and `05_verify`),
  each stage folder with a `CONTEXT.md`

## What is **not** in here

- No `00_actor-goal/` stage. That stage is system-level and belongs only
  in `features/_system/`. Do not create it inside a UC folder.
- No example artefacts. Do not copy `features/UC-00-login/output/*` into a
  new feature; derive your own from the actor/goal stage.
- No feature-specific `README.md` content. Replace the starter `README.md`
  with one that explains your new feature.
