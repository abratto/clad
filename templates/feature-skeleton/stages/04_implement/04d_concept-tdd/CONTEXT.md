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

**Agent stance for this stage:** if a test you want to write requires
another concept's state, the test belongs in 04e, not here.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../04b_spec/output/` | 4 | SPEC slices to compile against |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R5 |

## Process

For each public action of each concept, write the **inner-loop** unit
test (red), then implement the concept until the test is green. Build
up a test-intent derivation map showing every action × outcome →
test. Honour R1 (no cross-concept imports) and R5 (every action emits
a flow token) throughout.

## Outputs

- `output/concept-test-derivation.md` — the test-intent map for concepts
- (Side effect:) `<Name>ConceptTest.java` and `<Name>Concept.java` (or profile equivalent) per concept

## Verify

- All concept tests green.
- No cross-concept imports.
- Every public concept action emits a flow token.
- **Cross-stage check (back):** every action listed in `04b/output/` has at least one row in the test-intent map.

## Gate

Default human approval.

## Next stage

→ [`../04e_sync-tdd/CONTEXT.md`](../04e_sync-tdd/CONTEXT.md) — Inner red→green per sync (turns the outer flow test green)

To advance, the human says: **"Proceed to Stage 04e."**
