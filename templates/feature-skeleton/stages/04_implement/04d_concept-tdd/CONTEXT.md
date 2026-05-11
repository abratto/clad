# Stage 04d — Concept TDD (inner red → green)

## Why this stage exists

The **inner red→green** for each concept in isolation. One concept,
one test fixture, no other concepts in scope (R1). Doing concept TDD
*before* sync TDD (04e) means each concept's behaviour is locked down
before any coordination is asserted on top of it; otherwise sync
failures and concept failures look identical and the agent debugs the
wrong layer.

**Feeds:**

- `concept-test-derivation.md` → 04e (which concept actions can be relied on as already-green when wiring sync TDD); 05 (which actions are exercised by tests vs. only by syncs).
- `<Name>ConceptTest.java` + `<Name>Concept.java` → the running concept layer.

**Agent stance for this stage:**
- If a test you want to write requires another concept's state, the test belongs in 04e, not here.
- Write tests first. Do not write implementation code until the tests are approved (R8). Do not present tests and implementation together.
- Do not use in-memory substitutes (e.g. `HashMap`) for the profile's storage layer. Check `04a/output/` for the correct storage shape.
- Before writing each test, ask: "what state must exist for this outcome to be reachable?" Outcomes that require prior state (e.g. `ACCOUNT_EXISTS`, `AccountNotFound`) need an Arrange step that seeds that state before calling the action under test. A test that asserts an outcome it cannot produce from a fresh instance is a defect in the test.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../04b_spec/output/` | 4 | SPEC slices to compile against |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R5 |

## Process

For each public action of each concept, follow the **strict red→green
sequence** (hard rule R8). Do not batch tests and implementation:

1. **Write the test file(s) only.** Cover every action × outcome from
   the SPEC slice (`04b/output/`). Do not write any implementation code.
2. **Stop. Present the tests to the human. Wait for approval.**
   Do not proceed until the human explicitly approves the tests.
3. **Write the implementation** to make the approved tests green.
   The implementation must use the profile's storage layer as defined
   in `04a/output/` — not an in-memory substitute (e.g. no `HashMap`
   standing in for a named graph in the Jena profile).
4. **Stop. Present the implementation to the human. Wait for approval.**

Build up a test-intent derivation map showing every action × outcome →
test. Honour R1 (no cross-concept imports) and R5 (every action emits
a flow token) throughout.

## Outputs

- `output/concept-test-derivation.md` — the test-intent map for concepts
- (Side effect:) `<Name>ConceptTest.java` and `<Name>Concept.java` (or profile equivalent) per concept

## Verify

- All concept tests green.
- No cross-concept imports.
- Every public concept action emits a flow token.
- Tests were approved red before implementation was written (R8).
- **Cross-stage check (back):** every action listed in `04b/output/` has at least one row in the test-intent map.

## Gate

Default human approval.

## Next stage

→ [`../04e_sync-tdd/CONTEXT.md`](../04e_sync-tdd/CONTEXT.md) — Inner red→green per sync (turns the outer flow test green)

To advance, the human says: **"Proceed to Stage 04e."**
