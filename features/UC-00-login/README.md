# UC-00 — Login

A worked example use case. It is the simplest thing CLAD can be applied
to that is still meaningfully more than a "hello world": authenticate a
user with a username and a password, and on success establish a
session token they can present on subsequent requests.

It is intended for **reading**, not running. The point is to show the
shape of a feature folder under CLAD/Legible/ICM, end to end.

## What's here

- [`_config/voice.md`](_config/voice.md) — feature-scoped reference (tone of error messages)
- [`stages/00_actor-goal/`](stages/00_actor-goal/) — actor + goal definition
- [`stages/01_usecase/`](stages/01_usecase/) — the use case spec
- [`stages/02_concepts/`](stages/02_concepts/) — three concepts: `User`, `PasswordAuth`, `Session`
- [`stages/03_syncs/`](stages/03_syncs/) — `LoginGrantsSession` (active) + `LockoutOnFailedAttempts` (spec-only)
- [`stages/04_implement/`](stages/04_implement/) — router; sub-stages `04a_orm` (N/A), `04b_spec`, `04c_flow-tests`, `04d_concept-tdd`, `04e_sync-tdd`
- [`stages/05_verify/`](stages/05_verify/) — predicted token-tree walk for each scenario

## Reading order

1. [`stages/00_actor-goal/output/actors.md`](stages/00_actor-goal/output/actors.md) and [`goals.md`](stages/00_actor-goal/output/goals.md)
2. [`stages/01_usecase/output/usecase.md`](stages/01_usecase/output/usecase.md)
3. [`stages/02_concepts/output/`](stages/02_concepts/output/) — three `.concept.md` files
4. [`stages/03_syncs/output/`](stages/03_syncs/output/) — both `.sync.md` files
5. [`stages/04_implement/04b_spec/output/`](stages/04_implement/04b_spec/output/) — three SPECs
6. [`stages/04_implement/04c_flow-tests/output/login-flow-test.md`](stages/04_implement/04c_flow-tests/output/login-flow-test.md)
7. [`stages/04_implement/04d_concept-tdd/output/concept-test-derivation.md`](stages/04_implement/04d_concept-tdd/output/concept-test-derivation.md)
8. [`stages/04_implement/04e_sync-tdd/output/sync-test-derivation.md`](stages/04_implement/04e_sync-tdd/output/sync-test-derivation.md)
9. [`stages/05_verify/output/verification-trace.md`](stages/05_verify/output/verification-trace.md)
10. [`reference-impl/java-micronaut-jena/`](../../reference-impl/java-micronaut-jena/) — minimal Java stubs honouring R1–R5 (ArchUnit-checked)

## Status

Spec-complete; implementation is scaffolding. The Java profile compiles
and `mvn test` runs the ArchUnit suite, but the `LoginFlowTest` is
`@Disabled` until the inner-loop tests in `04d` and `04e` ship.
