# Stage 04d — Concept TDD (UC-00-login)

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
