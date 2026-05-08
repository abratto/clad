# Changelog

All notable changes to this repository will be documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it reaches 1.0.

Pre-1.0 minor versions can include incompatible methodology changes; the
file `methodology/` is the source of truth for what each version contains.

## [Unreleased]

## [0.1.0] — 2026-05-07

Initial public seed.

### Methodology

- **CLAD core** (`methodology/core/`): `CLAD.md`, `CONTRACTS.md`,
  `ARTEFACTS.md`, `ITERATIVE_CHANGES.md`.
- **Legible / WYSIWID architecture** (`methodology/architecture/`):
  `LEGIBLE.md`, `CONCEPTS.md`, `SYNCHRONIZATIONS.md`, `SYNC_PATTERNS.md`,
  `WEB_CONCEPT.md`, `ENGINE.md`, `MENTAL_MODEL.md`, `ARTEFACT_MAP.md`,
  `FLOW_TOKENS.md`, `ORM_NOTES.md`.
- **ICM implementation** (`methodology/implementation/`): `STAGES.md`
  (00 → 05 with 04a–04e sub-stages), `RULES.md` (the five hard rules),
  `QUALITY_GATE.md` (local pre-commit), `DELIVERY.md` (trunk-based +
  CI gate).
- **Optional overlays** (`methodology/overlays/`): `TRACKING.md` and
  `DECISIONS.md`.
- **Worked example**: `features/UC-00-login/` taken end-to-end through
  Stage 04 (Stage 05 closure pending). Annotated session walkthrough at
  `methodology/WALKTHROUGH.md`.

### Repository scaffold

- Canonical agent guide at `AGENTS.md`; thin adapters at `CLAUDE.md`,
  `.github/copilot-instructions.md`, `.cursor/rules/clad.mdc`.
- Workspace router at `CONTEXT.md`.
- Templates at `templates/` (incl. `templates/feature-skeleton/` for
  bootstrapping new features).
- Optional Java profile at `reference-impl/java-micronaut-jena/`.

### Tracking overlay

- Seeded `ROADMAP.md` at repo root (CI-checked, opt-out by deletion).
- "After cloning" one-time-setup checklist in `CONTRIBUTING.md`.

### CI

GitHub Actions workflow `.github/workflows/ci.yml` with four jobs:

- `markdown-links` — link check across all `*.md`.
- `hard-rule-r1` — bash grep enforcing R1 (no cross-concept imports)
  across `reference-impl/**/*.java`.
- `tracking-hygiene` — enforces `ROADMAP.md` conventions (≤1 `doing`
  row; resume point present; `Last updated` no older than 60 days).
- `java-verify` — conditional `mvn verify` when the Java profile's
  `pom.xml` is present.

### Notes

This release is the **seed** — usable as a `Use this template`
starter. The broader reference implementation lives at
[`abratto/tastetag`](https://github.com/abratto/tastetag) (private)
and will be ported into `reference-impl/` over subsequent releases.

[Unreleased]: https://github.com/abratto/clad/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/abratto/clad/releases/tag/v0.1.0
