# TDD discipline — London School outside-in double-loop

CLAD uses **London School TDD** (also called outside-in or mockist TDD).
This document is the canonical reference for what that means inside the
methodology. Every agent running stages 04c, 04d, or 04e must read this
before writing a single test.

## The two loops

```
 Outer loop (04c → 04e)
 ┌─────────────────────────────────────────────────────────┐
 │  Write a failing flow test for each use-case scenario.  │
 │  This test stays RED until the end of 04e.              │
 │                                                         │
 │   Inner loop (04d — repeat per concept)                 │
 │   ┌───────────────────────────────────────────────┐     │
 │   │  RED:   write concept unit tests              │     │
 │   │  GREEN: write concept implementation          │     │
 │   └───────────────────────────────────────────────┘     │
 │                                                         │
 │   Inner loop (04e — repeat per sync)                    │
 │   ┌───────────────────────────────────────────────┐     │
 │   │  RED:   write sync tests                      │     │
 │   │  GREEN: write sync implementation             │     │
 │   │  OUTER LOOP GOES GREEN here                   │     │
 │   └───────────────────────────────────────────────┘     │
 └─────────────────────────────────────────────────────────┘
```

## What London School means — and how it differs from Detroit School

| Property | London School (CLAD) | Detroit / Classicist |
|---|---|---|
| **Test order** | Outside-in: acceptance test first, unit tests derived from it | Inside-out: unit tests first, integration last |
| **What drives unit test design** | The outer (flow) test — you test what the scenario needs | The unit's own spec in isolation |
| **Collaborator isolation** | Concepts are isolated from each other in unit tests (R1) | Real objects preferred; mocks used sparingly |
| **When does everything go green?** | Outer loop goes green only when all inner loops are complete | Each unit goes green independently |
| **Failure signal** | A red flow test means a scenario is not yet delivered | A red unit test means a unit is broken |

The key implication for CLAD: **you do not design concept tests by reading
the concept spec alone.** You read the flow test spec first, identify which
concept actions the scenario needs to exercise, and derive the unit tests
from that. The flow test is the acceptance criterion; the unit tests are the
design scaffold.

## Stage 04 is executable, not documentary

Stage 04 is not complete because the markdown derivation files exist.
Those files are evidence and review aids. Completion requires the
sub-stage's executable side effects too:

- `04b`: SPEC slices that later tests compile against.
- `04c`: per-scenario stub flow tests plus executed compilation proof.
- `04d`: executable red concept tests, then concept implementation that
   turns them green.
- `04e`: executable red sync tests, then sync implementation that turns
   both sync tests and outer flow tests green.

If an agent claims a Stage 04 sub-stage is done without the required
test/source files or without executed command evidence, that claim is
invalid.

## Stage 04 order and gates are mandatory

The order is `04b -> 04c -> 04d -> 04e` (with optional `04a` before
them). `04b` is not optional when later stages consume SPECs.

Do not collapse these gates:

- **`04c` stops after flow test specs/stubs and waits for human
   approval (Gate 3).** This is the last design-stage human gate —
   the Gherkin `.feature` file IS the executable use case.
- `04d` and `04e` auto-advance because their tests are mechanically
   derived from already-approved artefacts (04c flow tests, 04b SPECs,
   chain tables, sync specs). The quality-gate scripts serve as the
   automated gate between red and green phases.
- The flow tests enabled at 04e-green must all pass before Stage 05.

For multi-model workflows, treat `04d` and `04e` as structural handoff
boundaries with their own child-stage folders:

- red phase: an architect/engineer model interprets upstream artefacts
   into executable tests
- green phase: an implementor model treats the approved tests as the
   immediate contract and writes code only to satisfy them

Name these subcontracts explicitly when reasoning about handoff:

- `04d-red` / `04d-green`
- `04e-red` / `04e-green`

In the stage tree, these map to real ICM child stages:

- `04d_concept-tdd/04d_red-tests/` then `04d_concept-tdd/04d_green-impl/`
- `04e_sync-tdd/04e_red-tests/` then `04e_sync-tdd/04e_green-impl/`

Green work may consult earlier prose/spec artefacts as reference, but
it may not redesign approved tests. If green discovers that the tests
are wrong, the work returns to the red phase or to the earliest invalid
upstream stage.

The red phase is not complete until it produces both:

- a derivation map showing every test's source in approved outer tests
   and/or SPEC rows
- a red-to-green handoff bundle naming the exact files, symbols, and
   command the implementor model must pick up

## The outer loop must stay red through 04d

This is not a flaw — it is the mechanism. The flow test is `@Disabled` (stub)
through stages 04c and 04d. It is enabled and expected to go green only at
the end of 04e, when the sync wiring is in place. If a flow test goes green
before 04e is complete, either the test is wrong or a sync was implemented
prematurely.

Do not be tempted to make the outer loop green early. An early-green flow
test is a false signal.

## How to derive inner-loop (concept) tests from the outer loop

For each concept action that appears in the flow test's token chain:

1. **Read the flow token entry** for that action. The outcome value (e.g.
   `VALID`, `ACCOUNT_EXISTS`) is one test case.
2. **Read the SPEC slice** (`04b_spec/output/`) for that concept. Every
   outcome listed in the SPEC is a required test case, whether or not it
   appears in the happy-path flow test.
3. **Ask: what state must exist for this outcome to be reachable?**
   - If none → `preconditions: none`
   - If prior state is required → add an Arrange step using the concept's
     own public API (not direct storage writes).
4. One test method per (action × outcome) pair.

The result is a test-intent derivation map — see
[`../../templates/test-intent-derivation-map.md`](../../templates/test-intent-derivation-map.md).

## Collaborator isolation in concept tests (R1 companion)

In the inner loop (04d), each concept is tested **in complete isolation**.
No other concept's code is loaded. No sync runs. The concept is instantiated
directly and its public actions are called directly.

This is not just an R1 compliance requirement — it is a diagnostic property.
If a concept test fails in 04d, the defect is in that concept. If a flow
test fails in 04e after all concept tests are green, the defect is in a sync.
This separation is what makes the failure signal useful.

## What Detroit School looks like (and why CLAD rejects it)

Detroit-style TDD in this context would mean:

- Writing `AccountTest` by reading `Account.concept.md` and testing every
  method without reference to what the flow test needs.
- Writing integration tests only after all units are green.
- Letting units call each other in tests as long as there are no mocks.

The problem: a Detroit-style agent will write tests that satisfy the concept
spec but miss what the scenario actually needs. Flow tests added later may
reveal that the wrong outcomes were implemented or that the token chain
doesn't match. By then the implementation is already written.

London School forces the question "does this scenario pass?" before any
implementation is written, which is exactly what CLAD's legibility property
requires.

## Test naming

CLAD uses London School BDD naming conventions for concept and sync
unit tests (Stages 04d and 04e). Flow tests (Stage 04c) use Gherkin
`.feature` files with scenario-level naming.

See [`../../templates/test-intent-derivation-map.md`](../../templates/test-intent-derivation-map.md)
for the full conventions:

- **Class name:** `<Concept><Action>Test` or `<SyncName>Test`
- **`@Nested` classes:** `When<Precondition>` / `When<Trigger>` group outcomes
- **Method name:** `should<Behavior>When<Condition>` or `should<Trigger><Then>`
- **Comment blocks:** `// GIVEN` / `// WHEN` / `// THEN` (Given-When-Then)
- **Assertions:** verify interactions (outcome type, scheduled actions), not
  internal state
- **Ubiquitous language:** use terms from concept specs and use cases

## Capability profiles

CLAD defines three capability profiles that apply during Stage 04
(see `AGENTS.md §7`):

| Profile | Stages | Fence |
|---|---|---|
| Red (test derivation) | 04c, 04d-red, 04e-red | Tests and derivation maps only — no implementation code |
| Green (implementation) | 04d-green, 04e-green | Implementation only — do not rewrite approved tests |

This boundary is also the recommended model-switch point in multi-model
workflows: use a design/derivation-capable model in red, and an
implementation-capable model in green.

**Do not switch from red to green without explicit human approval.**
Approval is a statement like "approved — proceed to implementation" or
"approved — proceed to 04e". Silence, a question, or "looks good" is
not approval.
