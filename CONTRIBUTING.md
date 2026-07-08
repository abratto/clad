# Contributing to CLAD

Thanks for your interest. CLAD is a methodology repository: most contributions
are documentation, templates, and worked examples, not application code.

## Ground rules

1. **Every change is led by a contract.** If you are adding a feature, start
   at Stage 00 (`features/UC-XX/stages/00_actor-goal/`) and walk the stages
   in order; the use case is the Stage 01 artefact, not the starting point.
   If you are adding methodology content, open an issue describing what gap
   you are filling before writing prose.
2. **Every change produces a reviewable artefact.** Markdown, YAML/JSON
   schemas, code under `reference-impl/`. No invisible state.
3. **No cross-concept references.** See [`AGENTS.md`](AGENTS.md) §5 for the
   full hard-rules list. Enforced in any code under `reference-impl/`.
4. **Cite your sources.** If you draw on Meng & Jackson, Van Clief, or any
   other external work, add the citation to `NOTICE` and to the relevant
   `methodology/reference/` file.

## Workflow

1. Open an issue or discussion. State the use case in one paragraph.
2. Fork or branch (`feat/UC-XX-short-name` or `docs/topic`).
3. For new feature work, first run system-scope Stage 00 at
   [`features/_system/stages/00_actor-goal/CONTEXT.md`](features/_system/stages/00_actor-goal/CONTEXT.md).
   After the Stage 00 gate passes, copy [`templates/feature-skeleton/`](templates/feature-skeleton/)
   to `features/UC-XX-<slug>/` and start at `stages/01_usecase/CONTEXT.md`.
   Do **not** copy `features/UC-00-login/` — that is the worked example,
   kept for reading. For methodology edits, keep diffs focused; do not
   bundle unrelated changes.
4. Open a PR. Link the issue. Describe what contract drove the change and
   what artefact it produced.

## After cloning — one-time setup

**Install the local stage-sequence hook (strongly recommended).** Run
this once so `git commit` refuses commits that skip a CLAD stage or
decouple an implementation from its spec:

```bash
./quality-gate/install-hooks.sh
```

It sets `git config core.hooksPath .githooks` for your clone. The hook
is opt-in (git never runs hooks from a fresh clone), but it is the
cheapest way to keep the stage pipeline honest — see
[`methodology/implementation/QUALITY_GATE.md`](methodology/implementation/QUALITY_GATE.md)
§"Installing the local pre-commit hook". Bypass a single commit with
`git commit --no-verify`.

The methodology runs the same with or without GitHub-side tracking. If you
do want the tracking overlay (recommended for any project that will live
longer than one feature), do this once after cloning:

1. **Edit [`ROADMAP.md`](ROADMAP.md).** Replace the seed `UC-01-<slug>`
   row with your first real feature. Keep exactly one row at status
   `doing` at any time. CI enforces this — see
   [`methodology/overlays/TRACKING.md`](methodology/overlays/TRACKING.md).
2. **Enable Issues** on the repo (Settings → Features).
3. **Create the three labels** referenced by the issue templates and
   `TRACKING.md`: `clad:in-progress`, `clad:done`, `clad:spec-needed`.
   (The first two issues you file from the templates will fail to
   apply labels until these exist.)
4. **Create one GitHub Project** (Projects → New project → Board).
   Suggested columns: `Backlog` · `Doing` · `In review` · `Done`.
   Link it from your `ROADMAP.md` Backlog section if you want a single
   entry point.
5. **Update `ROADMAP.md` at the end of every working session.** The
   `Resume point` block is the cheapest cross-session memory you have;
   CI flags it as stale after 60 days.

If you don't want the overlay, **delete `ROADMAP.md`** — the
`tracking-hygiene` CI job is a no-op when the file is absent.

## Branching & merging

This repo is run trunk-based: `main` is the only long-lived branch and every
change lands via a short-lived PR. The full posture and the CI gate are in
[`methodology/implementation/DELIVERY.md`](methodology/implementation/DELIVERY.md).
Highlights:

- One PR = one change (one feature **or** one iterative change **or** one
  focused methodology edit). Don't bundle.
- Branches live hours, not weeks. If yours has been open more than two
  days, split it or rebase onto `main`.
- Branch names: `feat/UC-XX-<slug>`, `change/UC-XX-<slug>`,
  `docs/<topic>`, `impl/<profile>-<topic>`, `chore/<topic>`.
- Squash-merge. The git log carries one commit per PR; the per-stage
  history of a feature lives in the `stages/NN_*/output/` artefacts.
- CI must be green. The local
  [`methodology/implementation/QUALITY_GATE.md`](methodology/implementation/QUALITY_GATE.md)
  is the developer's mirror of CI; CI is authoritative.

## Public template governance (recommended)

If this repository is public and used as a template starter, keep
maintainer control by enabling branch protection on `main`:

- Require pull requests before merge.
- Require status checks to pass (use CI jobs from `.github/workflows/ci.yml`).
- Require review from Code Owners.
- Restrict direct pushes to `main`.

The baseline ownership map is in [`.github/CODEOWNERS`](.github/CODEOWNERS).
Update it as maintainership changes.

## Style

- Markdown: ATX headings, fenced code blocks with language tags, line wrap
  off (let the editor wrap).
- Filenames: `UPPER_SNAKE_CASE.md` for methodology documents,
  `lower-kebab-case.md` for everything else.
- Concepts and syncs in templates use PascalCase names
  (`User`, `PasswordAuth`, `LoginFlow`).

## License

By contributing you agree that your contribution is licensed under the
Apache License 2.0 (see [LICENSE](LICENSE)).
