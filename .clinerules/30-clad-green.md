# CLAD Green Rule

Use this rule only while implementing approved Stage `04d` or `04e` work.

## Mission

Write the implementation that makes approved red tests pass.
Do not modify approved test files unless the human explicitly reopens the red stage.
This is the implementor side of the Stage 04 handoff: treat the
approved tests as the immediate contract.

## Mandatory sequence

1. Read all approved test files for the concept or sync under implementation.
2. Extract the exact package declaration, class names, method signatures, enums, and referenced fields.
3. Read `.cline-clad-config` in the repo root.
   - If it is missing, stop and ask the human to create it from `.cline-clad-config.example`.
4. Read `features/UC-XX-<slug>/_config/package-and-layout.md` and obey `APP_PACKAGE_ROOT` and `APP_SOURCE_ROOT`.
5. Read `04a/output/` for the storage shape.
6. Read `04b/output/` for the spec and its complete outcome set.
7. Write the implementation to match the tests, package layout, storage profile, and spec.
8. Run the tests using `TEST_COMMAND` from `.cline-clad-config` until green.
9. Stop and wait for explicit human approval.

If the approved tests appear wrong, incomplete, or in tension with
earlier prose artefacts, stop and send work back to the red phase or
earliest invalid upstream stage. Do not redesign the tests during green
work.

## Hard constraints

- Package and file path must match `APP_PACKAGE_ROOT` and `APP_SOURCE_ROOT`.
- `com.example.app` is forbidden unless that exact package root is configured.
- No in-memory substitutes for the configured storage layer.
- Every spec outcome gets its own distinct code path.
- Every public action emits exactly one flow token at completion.
- No imports across concept packages.
- Do not rewrite approved tests during green work.
- Do not claim a green stage from markdown artefacts alone; the required source files and executed test command evidence must exist.
- In `04e`, implement exactly the approved Stage `03` sync set. Do not invent extra coordinator/sync classes that lack an upstream sync spec.
- Do not continue into the next Stage `04` sub-stage without explicit approval for the current green work.
- Do not reinterpret earlier prose/spec artefacts against approved tests
   in order to redesign the implementation contract.

## Approval boundary

Keep this rule enabled until the implementation is approved. Then disable it and return to the red rule for the next red stage, if any.
