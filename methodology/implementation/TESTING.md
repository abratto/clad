# Testing — spec-driven, test-verified

This document is the canonical reference for how tests work in CLAD. It
replaces the former London-School TDD document (DR-0001). Every agent
running Stage 04 must read it before writing a test.

## Why CLAD does not do in-loop TDD

CLAD separates **design** from **verification**. Design is settled in
Stages 01–03b and frozen as per-concept contracts at 04b; tests are a
mechanism for proving the implementation matches what was already
decided, not a mechanism for discovering the design.

The evidence for this is summarised in
[`../../docs/decisions/0001-spec-driven-testing.md`](../../docs/decisions/0001-spec-driven-testing.md)
and cited in [`../reference/CITATIONS.md`](../reference/CITATIONS.md)
(Böckeler, *TDD inside the agent loop*). In short: an agent performing
red-green-refactor inside its own loop gains no design benefit, costs
several times the tokens, and "watching a test go red" proves only that
the agent ran it — not that it failed for the right reason. The valuable
uses of tests to an agent are (a) **frozen, human-approved acceptance
expectations** and (b) **regression/effectiveness sensors**.

## The two verification surfaces

| Surface | Authored at | Purpose | Gate |
|---|---|---|---|
| **Acceptance Spec + native flow tests** | 04c | Frozen, human-readable scenarios; end-to-end proof the scenario runs | Gate 3 (human) |
| **Concept & sync unit tests** | 04d/04e | Isolated regression/effectiveness sensors for each concept and sync | mutation score |

There is no third surface. There is no Gherkin/Cucumber track: the flow
test is a native test in the profile's framework, and the Acceptance
Spec is the human-readable index of those tests.

## The Acceptance Spec is frozen

`04c_acceptance-tests/output/acceptance-spec.md` is the Gate-3 artifact.
It maps one section per use-case scenario to the native test method that
enforces it. It is a *derived view*: every value traces to the use case,
a chain table, a contract, or a sync spec.

Because Gate 3 approval is bound to the content hash of stages
`04a`/`04b`/`04c` (`verify_stage_sequence.py` `compute_gate_hash`), editing
the Acceptance Spec after approval **stales Gate 3** and forces the human
to re-approve the diff. That is the whole freeze mechanism — no separate
hash file is needed. `verify_acceptance_binding.py` additionally proves
the Spec is a truthful index: every scenario has a section, every
`Test:` binding resolves, and every `*FlowTest` method is documented.

## Tests are derived, and produced with the implementation

Stages 04d and 04e are **single** stages: the derivation map, the unit
tests, and the implementation are produced together. The tests derive
from already-approved artefacts:

- Every concept action × contract outcome is one unit test row
  (`concept-test-derivation.md`).
- Every sync is one unit test class asserting the actions it schedules
  (`sync-test-derivation.md`).

An agent that implements a concept or sync before the corresponding
tests exist has violated R8. The acceptance tests are the executable form
of the use case (approved at Gate 3 before any 04d/04e work).

## Test effectiveness is a mutation score

A green suite is not evidence that a test constrains the code. The
test-effectiveness signal is the **mutation score** of the concept and
sync suites:

- `clad.properties` `mutation.command` runs the profile's mutation tool
  and prints one line: `MUTATION_SCORE: <pct>` (or per-scope
  `MUTATION_SCORE.concepts:` / `MUTATION_SCORE.syncs:`) when it measured;
  `MUTATION_SKIP: <reason>` when the tool cannot run in this environment.
- `mutation.threshold` is the minimum acceptable score (default 80%).
- `verify_mutation_score.py` fails Stage 04d/04e below threshold. It
  **SKIPs** — visibly, not silently — when `mutation.command` is unset or
  the tool reports `MUTATION_SKIP`. It skips nothing when passed
  `--require` (or `mutation.require=true`): then a SKIP is a failure. The
  canonical profile pins PIT 1.30.0 (which supports current JDKs, including
  25); CI runs the gate with `--require` on JDK 21.

Neither a red-green ritual nor a test count substitutes for this signal.

## Concept isolation is still a diagnostic property (R1 companion)

In the unit loop, each concept is tested **in complete isolation**. No
other concept's code is loaded; no sync runs. The concept is
instantiated directly and its public actions called directly.

This is not merely R1 compliance — it is a diagnostic. If a concept unit
test fails, the defect is in that concept. If an acceptance test fails
in 04e after all concept tests are green, the defect is in a sync. The
isolation is what makes the failure signal useful; it does not depend on
any red-green ordering.

## Gate grades and evidence

Stage 04 evidence is:

- `04b`: contract slices the tests compile against.
- `04c`: the Acceptance Spec + native flow tests, plus compiled-test
  evidence.
- `04d`: concept unit tests + implementation; `verification-evidence.md`
  records the test run, contract-outcome coverage, and mutation score.
- `04e`: sync unit tests + implementation;
  `verification-evidence.md` records the test run, the now-green
  acceptance tests, and mutation score.

If an agent claims a Stage 04 stage is done without the required
test/source files or without executed command evidence, that claim is
invalid.

## Test naming (advisory)

CLAD recommends, but does not gate, these conventions for unit tests:

- **Class name:** `<Concept><Action>Test` or `<SyncName>Test`
- **`@Nested` classes:** `When<Precondition>` / `When<Trigger>`
- **Method name:** `should<Behavior>When<Condition>` or `should<Trigger><Then>`
- **Comment blocks:** `// GIVEN` / `// WHEN` / `// THEN`
- **Assertions:** the `outcome` and the primary completion field values
  (R14/R16), not internal state
- **Ubiquitous language:** terms from concept specs and use cases

`verify_test_naming.py` reports drift but is not a blocking gate:
prescribing *how* a suite is written is fragile across models and
releases; effectiveness (mutation) and coverage are what block.

## Capability profiles

| Profile | Stages | Fence |
|---|---|---|
| Design/acceptance | 04a, 04b, 04c | Acceptance Spec + tests; the human gate is here |
| Implementation | 04d, 04e | Implementation + unit tests |

Unlike the former red/green split, this is not a mandatory two-session
handoff: 04d and 04e may run in one session. A team that wants a
test/implementation separation may still use separate sessions, but CLAD
does not gate on it.
