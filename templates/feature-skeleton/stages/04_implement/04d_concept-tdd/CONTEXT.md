# Stage 04d — Concept TDD (inner red → green)

## Pre-condition (agent must verify before starting)

**`04c_flow-tests/output/` must be non-empty.** If it is empty, stop
immediately and tell the human that Stage 04c must be completed and
gated before Stage 04d can begin. Do not write any test or
implementation file until this pre-condition is satisfied.

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
- Read `methodology/implementation/TDD.md` before writing anything. Concept
  tests are derived from the flow test, not from the concept spec alone.
- If a test you want to write requires another concept's state, the test belongs in 04e, not here.
- Write tests first. Do not write implementation code until the tests are approved (R8). Do not present tests and implementation together.
- Do not use in-memory substitutes (e.g. `HashMap`) for the profile's storage layer. Check `04a/output/` for the correct storage shape.
- Before writing each test, ask: "what state must exist for this outcome to be reachable?" Outcomes that require prior state (e.g. `ACCOUNT_EXISTS`, `AccountNotFound`) need an Arrange step that sets up that state.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../04b_spec/output/` | 4 | SPEC slices to compile against |
| `../04c_flow-tests/output/` | 4 | Pre-condition check + drives test derivation |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R5 |
| `../../../../../methodology/implementation/TDD.md` | 3 | London School double-loop — how to derive concept tests from flow tests |

## Process

For each public action of each concept, follow the **strict red→green
sequence** (hard rule R8). Do not batch tests and implementation:

1. **Derive tests from the flow test first.** Read `04c_flow-tests/output/`
   and identify which outcomes for this concept are exercised by the flow
   tests. Then read the SPEC slice (`04b/output/`) and add any additional
   outcomes not covered by the flow tests. Every (action × outcome) pair
   in the SPEC is a required test case.
2. **Write the test file(s) only.** Do not write any implementation code.
   "Red" here means executable failing tests (not disabled placeholders,
   not compile-failing test suites).
   Run tests now and confirm failure is behavioral.
3. **Stop. Present the tests to the human. Wait for approval.**
   Do not proceed until the human explicitly approves the tests.
   Do not switch to `clad-green` mode until approval is given.
4. **Switch to `clad-green` mode.** Write the implementation to make the
   approved tests green. Before writing any code, read the approved test
   files and extract:
   - The exact package declaration
   - The exact class name being instantiated
   - Every method signature being called
   - Every inner class and enum being referenced

   Your implementation must match all of these exactly. Do not invent
   a different package, class name, or method shape.

   The implementation must also use the profile's storage layer as
   defined in `04a/output/` — not an in-memory substitute (e.g. no
   `HashMap` standing in for a named graph in the Jena profile).

   Cross-check the SPEC (`04b/output/`) and ensure every defined
   outcome has its own distinct code path (R9). Do not collapse two
   SPEC outcomes into one return value.
5. **Stop. Present the implementation to the human. Wait for approval.**
   Switch back to `clad-red` mode only after the human explicitly approves.

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
- Before implementation began, tests were executed and observed failing for behavioral reasons (true red), with successful test compilation.
- Tests were approved red before implementation was written (R8).
- Mode was switched to `clad-green` only after explicit human approval of tests.
- **Cross-stage check (back):** every action listed in `04b/output/` has at least one row in the test-intent map.
- **Cross-stage check (back):** `04c_flow-tests/output/` is non-empty (pre-condition was satisfied).
- **Cross-stage check (back):** every outcome exercised by the flow tests has a corresponding test row in the derivation map.

## Gate

Default human approval.

## Next stage

→ [`../04e_sync-tdd/CONTEXT.md`](../04e_sync-tdd/CONTEXT.md) — Inner red→green per sync (turns the outer flow test green)

To advance, the human says: **"Proceed to Stage 04e."**
