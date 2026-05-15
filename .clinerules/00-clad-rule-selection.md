# CLAD Rule Selection for Cline

Cline already reads `AGENTS.md`. These workspace rules are the Cline replacement for the old Roo custom modes.

## Toggle discipline

- Enable exactly one CLAD phase rule at a time in the Cline Rules panel:
  - `10-clad-architect.md` for Stages `00`-`03` and `05`
  - `20-clad-red.md` for Stages `04c`, `04d`, and `04e` test/spec work
  - `30-clad-green.md` for Stage `04d`/`04e` implementation after red-test approval
- If two CLAD phase rules are enabled at once, disable the one that does not match the current stage before continuing.
- Treat rule switches the same way Roo mode switches were treated: they happen only after explicit human approval at the stage gate.
- Stage `04` still runs one sub-stage at a time: `04b -> 04c -> 04d -> 04e` (with optional `04a` before them). Do not treat Stage `04` as one combined pass.

## Important limitation vs Roo

- Cline workspace rules guide behavior; they do not provide Roo-style `fileRegex` edit fences.
- Preserve the same boundaries as hard instructions:
  - architect rule: no implementation or tests
  - red rule: tests/specs only
  - green rule: implementation only, do not rewrite approved tests
- If a task would cross one of those boundaries, stop at the gate and ask the human which phase to run next.

## Local config

- Stage `04` implementation work reads `.cline-clad-config` from the repo root.
- If `.cline-clad-config` is missing, create it by copying `.cline-clad-config.example` and filling in the project-specific values before continuing.
- `.cline-clad-config` is per-developer and gitignored.
