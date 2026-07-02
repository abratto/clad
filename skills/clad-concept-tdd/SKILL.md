---
name: clad-concept-tdd
description: Execute concept-level TDD during CLAD Stage 04d. Use when deriving red concept tests from approved flow tests and SPECs, then implementing green concept classes that make those tests pass. Follows London School inner-loop discipline.
---

# CLAD Concept TDD (Stage 04d)

## What this skill covers

The inner (concept) loop of London School TDD: `04d-red` derives
executable concept unit tests from approved outer artefacts, and
`04d-green` implements only against those approved tests until green.

## Quick reference

Load these files:

1. `methodology/implementation/TDD.md` — London School handoff semantics,
   derivation rules, collaborator isolation
2. `methodology/implementation/RULES.md` — hard rules R1, R5, R8, R9,
   R14, R16
3. `templates/test-intent-derivation-map.md` — coverage template format
4. `features/UC-XX-<slug>/stages/02_concepts/output/` —
   concept specs
5. `features/UC-XX-<slug>/stages/04b_spec/output/` —
   SPEC slices
6. `features/UC-XX-<slug>/stages/04c_flow-tests/output/` —
   approved flow tests (drives derivation)
7. `features/UC-XX-<slug>/_config/build-and-test.md` —
   canonical test command
8. `features/UC-XX-<slug>/_config/package-and-layout.md` —
   canonical package/source-root settings
9. `reference-impl/java-micronaut-jena/README.md`,
   `reference-impl/java-micronaut-jena/CODE_STYLE.md`,
   `reference-impl/java-micronaut-jena/SYNC_LOWERING.md`, and
   `reference-impl/java-micronaut-jena/CANONICAL_EXEMPLAR.md` — profile
   conventions (only when this profile is selected)
10. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. **04d-red**: Derive concept tests from approved `04c` flow tests
   and `04b` SPECs. Write test files under `APP_TEST_SOURCE_ROOT`.
   Run red — compilation succeeds, tests fail behaviorally.
   Record the derivation map and handoff bundle.
2. **04d-green**: Read the approved red tests. Extract exact packages,
   class names, and signatures. Implement only what is needed to make
   tests pass. Do not redesign approved tests.

## Field-value assertion requirement

Every concept unit test must include field-value assertions. After
asserting the outcome token, assert the primary fields that
`writeCompletion` writes and that downstream syncs will consume.

```java
// Insufficient - only asserts outcome token
assertThat(completion.binding("outcome")).isEqualTo("FOUND");

// Required - also asserts the fields downstream syncs will read
assertThat(completion.binding("outcome")).isEqualTo("FOUND");
assertThat(completion.binding("slug")).isEqualTo(inputSlug);
assertThat(completion.binding("title")).isNotEmpty();
assertThat(completion.binding("authorId")).isNotEmpty();
```

Silent field-mapping bugs (wrong variable name, PSS substitution
collision, missing SPARQL binding) return null values for downstream
consumers without causing any exception. An outcome-only test will pass;
a field-value test will catch the null immediately.

## Hard constraints

- **Red phase**: tests and derivation maps only — no implementation code.
- **Green phase**: implementation only — do not rewrite approved tests.
- One test class per concept action.
- Every concept unit test asserts the outcome and the primary completion
   field values that downstream syncs consume.
- No cross-concept imports (R1).
- Every public action emits a flow token (R5).
- Distinct SPEC outcomes remain distinct in code paths (R9).
- Do not substitute an in-memory store for the configured storage layer.
- Use the exact package/source-root from `_config/package-and-layout.md`.

## Test naming (London School BDD)

Follow the London School outside-in convention for concept unit tests:

- **Class name:** `<Concept><Action>Test` (e.g. `UserLookupByUsernameTest`)
- **`@Nested` class:** `When<Precondition>` groups outcomes by required state
  (e.g. `WhenUserExists`, `WhenUserUnknown`)
- **Method name:** `should<Behavior>When<Condition>` uses business language
  (e.g. `shouldReturnUserId`, `shouldReturnNotFound`)
- **Assertions:** verify interactions — outcome type, flow token presence —
  not internal concept state
- **Comment blocks:** `// GIVEN` / `// WHEN` / `// THEN` instead of
  Arrange-Act-Assert
- **Ubiquitous language:** use terms from the concept spec and use case,
  not technical jargon (`shouldReturnUserId`, not `shouldReturnHttp200`)

```java
class UserLookupByUsernameTest {
    @Nested class WhenUserExists {
        @Test void shouldReturnUserId() {
            // GIVEN: a user "ada" is registered
            // WHEN: lookupByUsername("ada") is called
            // THEN: outcome is FOUND with the user's userId
        }
    }
    @Nested class WhenUserUnknown {
        @Test void shouldReturnNotFound() {
            // GIVEN: no user named "nobody" exists
            // WHEN: lookupByUsername("nobody") is called
            // THEN: outcome is UNKNOWN
        }
    }
}
```
