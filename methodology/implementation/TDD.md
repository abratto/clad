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

## Mode switching in Roo

The red→green boundary maps directly to Roo mode switches:

| What just happened | Mode to be in |
|---|---|
| Starting 04c, 04d (tests), or 04e (tests) | `clad-red` |
| Human has **explicitly approved** the red tests | Switch to `clad-green` |
| Human has **explicitly approved** the green implementation | Switch back to `clad-red` for the next stage |

**Do not switch modes without explicit human approval.** Approval is a
statement like "approved — proceed to implementation" or "approved — proceed
to 04e". Silence, a question, or "looks good" is not approval.
