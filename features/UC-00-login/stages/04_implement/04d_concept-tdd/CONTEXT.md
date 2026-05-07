# Stage 04d — Concept TDD (UC-00-login)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../04b_spec/output/` | 4 | SPEC slices |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../methodology/implementation/RULES.md` | 3 | R1, R5 |

## Process

Drive each concept (`User`, `PasswordAuth`, `Session`) outside-in
with a unit test per public action × outcome. Honour R1 (no cross-
concept imports) and R5 (every action emits a flow token).

## Outputs

- `output/concept-test-derivation.md`
- (Side effect:) `<Name>ConceptTest.java` and `<Name>Concept.java` under the Java profile

## Verify

- All concept tests green.
- No cross-concept imports (also enforced by `LegibleArchitectureRulesTest` R1).
- Every public concept action emits a flow token (also enforced by R5).
- **Cross-stage check (back):** every action in `04b/output/` has at least one row in the test-intent map.

## Gate

Default.
