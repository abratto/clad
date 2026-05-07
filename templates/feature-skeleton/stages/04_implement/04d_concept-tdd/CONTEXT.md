# Stage 04d — Concept TDD (inner red → green)

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
