# Contributing to CLAD

Thanks for your interest. CLAD is a methodology repository: most contributions
are documentation, templates, and worked examples, not application code.

## Ground rules

1. **Every change is led by a contract.** If you are adding a feature, start
   with a use case (`features/UC-XX/stages/01_usecase/output/usecase.md`).
   If you are adding methodology content, open an issue describing what gap
   you are filling before writing prose.
2. **Every change produces a reviewable artefact.** Markdown, YAML/JSON
   schemas, code under `reference-impl/`. No invisible state.
3. **No cross-concept references.** This is enforced in any code under
   `reference-impl/`. See `methodology/implementation/RULES.md`.
4. **Cite your sources.** If you draw on Meng & Jackson, Van Clief, or any
   other external work, add the citation to `NOTICE` and to the relevant
   `methodology/reference/` file.

## Workflow

1. Open an issue or discussion. State the use case in one paragraph.
2. Fork or branch (`feat/UC-XX-short-name` or `docs/topic`).
3. For new features, use the ICM stage scaffold in
   `features/UC-00-login/` as a template. For methodology edits, keep
   diffs focused; do not bundle unrelated changes.
4. Open a PR. Link the issue. Describe what contract drove the change and
   what artefact it produced.

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
