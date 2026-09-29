# Build & test command (profile hook)

This file exists to prevent ambiguity about *how to run tests in this repo*.

Agents (and humans) must not guess which tool to use.

## Required: declare the canonical build-and-test command

Write **one** command that:

1. Builds/compiles the project (including test sources)
2. Executes the test suite (or the default test task)

Example shapes (choose the one that matches your repo):

- Maven: `mvn test`
- Gradle: `./gradlew test`
- Node: `npm test`
- Python: `pytest`
- Go: `go test ./...`

If your project is multi-module, specify the directory you run it from.

## Optional: targeted test command

If your stack supports running a single test class / package, include an example here.

## Used by CLAD stages

Stages that require executed evidence (not just intent):

- **04c**: prove the native acceptance tests compile (they may be `@Disabled` until implementation lands).
- **04d/04e**: tests and implementation are produced together — there is no red/green split. Test effectiveness is gated by `mutation.command`/`mutation.threshold` (see `TESTING.md`); a suite that passes but kills few mutants does not constrain the code. `@Disabled`/skipped is never acceptable evidence.
- **04e gate**: provide executed evidence that tests compile and that sync unit tests + native acceptance tests are green.
