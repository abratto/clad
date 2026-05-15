# CLAD Red Rule

Use this rule only while writing red artefacts in Stage `04c`, `04d`, or `04e`.

## Mission

Write failing tests or stage output specs only:
- flow test specs (`04c`)
- concept tests (`04d`)
- sync tests (`04e`)

Do not write implementation code.

## Read order

Before writing anything:
1. Read `methodology/implementation/TDD.md`.
2. Read `methodology/architecture/FLOW_TOKENS.md`.
3. Read the current stage `CONTEXT.md`.
4. Load only the files listed in that stage's `Inputs` table.

## Hard constraints

- Tests/specs only. No implementation classes, not even stubs.
- Do not present tests and implementation together.
- Derive tests from the approved flow specs first, then the concept spec.
- Before writing each test, ask what prior state is required for the outcome to be reachable.
- One test class per concept action.
- Keep the package aligned with the package under test.
- Do not skip `04b_spec`. If the SPEC slice is missing, stop instead of deriving tests from prose.
- `04c` requires both markdown specs and per-scenario stub flow test files. Markdown alone does not complete the stage.
- `04d`/`04e` red means executable failing tests with successful compilation, not markdown-only derivations and not compile-failing suites.
- Do not merge `04c`, `04d`, and `04e` into one pass. Stop at each written gate and wait for explicit approval.

## Approval boundary

Do not disable this rule and enable green until the human explicitly approves the red tests.
