# DR-0001 — Spec-driven testing: frozen acceptance spec + mutation gate over in-loop TDD

**Status:** Accepted

**Date:** 2026-09-28

## Context

CLAD's Stage 04 currently runs a London-School outside-in double loop: a
Gherkin `.feature` flow test at 04c, then red→green concept sub-stages at
04d and sync sub-stages at 04e. Böckeler's *TDD inside the agent loop*
(and the empirical work it cites: WebApp1K, TDAD, TGen) finds that
fine-grained TDD performed entirely inside an agent's own loop does not
improve design — non-TDD runs that front-loaded the whole design scored
equal or better — while costing several times the tokens, and that
watching a test go red proves only that the agent ran it when the agent
writes both test and code. The valuable uses of tests in an agent loop
are as frozen, human-approved acceptance expectations and as
regression/effectiveness sensors, not as a design-discovery process.

CLAD already front-loads design (stages 00–03b), freezes contracts at
04b, and derives unit tests mechanically from approved artefacts (R8).
Its exposure is therefore not the *philosophy* but the *ceremony*: the
red/green sub-stage split, the failure-class and SHA-256 continuity
riders, the red→green handoff bundle, and the Cucumber/step-definition
derivation grammar — all of which police process shape rather than
outcome quality, and none of which measure whether the tests are any
good.

## Decision

Replace Stage 04's in-loop TDD ritual with a spec-driven, test-verified
model:

1. Collapse `04d-red/green` and `04e-red/green` into single
   `04d_concept-impl` / `04e_sync-impl` stages that produce tests and
   implementation together. Drop the red/green evidence apparatus, the
   handoff bundle, and test-file continuity.
2. Replace the Gherkin/Cucumber outer track with native per-scenario
   flow tests (execution) plus a generated, **frozen Acceptance Spec**
   (legibility). The Acceptance Spec is the Gate-3 human artifact; a
   checker enforces 1:1 binding between its rows and the native test
   methods, and any expectation change forces human re-approval of the
   diff (the "Approved Scenarios" pattern).
3. Make **mutation score the test-effectiveness gate** for the concept
   and sync unit suites (blocking threshold, configurable), replacing
   "prove it went red" as evidence that a test bites.

## Consequences

- Four verification surfaces (flow, step-defs, concept, sync) collapse to
  two (native acceptance tests, mutation-gated unit tests) with one
  frozen, human-readable index between them.
- Legibility improves: the non-programmer navigates `usecase.md` →
  `acceptance-spec.md` → (optional) `contract.md` → `chain-table.md`
  without reading code, instead of being separated from the executable
  layer by an uninspectable derivation grammar.
- Multi-model architect/implementor handoff is dropped; the red/green
  split no longer exists as a gated boundary.
- The test suite acquires a real quality signal (mutation) where it
  previously had only coverage and field-assertion checks.
- Mutation testing adds runtime cost and needs threshold calibration.
- Gherkin-era clones and legacy Stage 04 trees are rejected, not
  migrated; this is a breaking methodology change requiring a major
  version bump and a migration note.
- `methodology/implementation/TDD.md` becomes `TESTING.md`; R8 is
  rewritten and R16 retired into R14.

## References

- Birgitta Böckeler, *TDD inside the agent loop — theater or actual
  value?*, martinfowler.com, 2026. See `CITATIONS.md`.
- WebApp1K benchmark (2025); Test-Driven Agentic Development / TDAD
  (2026); TGen (2024) — cited in the article and the analysis that
  motivated this decision.
- `maintenance/spec-driven-testing-and-acceptance-spec.md` — the
  implementation record for this decision.
