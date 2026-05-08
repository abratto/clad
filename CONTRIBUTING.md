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
3. For new features, copy [`templates/feature-skeleton/`](templates/feature-skeleton/)
   to `features/UC-XX-<slug>/` and start at
   `stages/00_actor-goal/CONTEXT.md`. Do **not** copy
   `features/UC-00-login/` — that is the worked example, kept for reading.
   For methodology edits, keep diffs focused; do not bundle unrelated
   changes.
4. Open a PR. Link the issue. Describe what contract drove the change and
   what artefact it produced.

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
