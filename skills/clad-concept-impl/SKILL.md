---
name: clad-concept-impl
description: Implement business concepts and their unit tests during CLAD Stage 04d. Use when deriving concept tests from approved contracts and the 04c Acceptance Spec, then producing the concept implementation alongside them in a single stage. Test effectiveness is gated by mutation score.
---

# CLAD Concept Implementation (Stage 04d)

> **Role:** required stage guidance for Stage 04d. The stage `CONTEXT.md`
> `Inputs` table is authoritative for *which files to load*; load those
> exactly. Follow the canonical `java-legible` (fire-after-commit)
> profile's conventions.

## What this skill covers

Stage 04d is a **single stage**: the concept unit tests and the concept
implementation are produced together. There is no red/green sub-stage
split and no handoff bundle. The tests derive from already-approved
artefacts — the Stage 04b contracts and the 04c Acceptance Spec — and are
verification, not design. Read `TESTING.md` first.

## Files

The stage `CONTEXT.md` `Inputs` names the loading set: the canonical concept
specs (`features/_system/concepts/`), this feature's `02` proposals and
`concept-bindings.md`, `04b` contracts, the `04c` Acceptance Spec,
`03` sync specs, `_config/build-and-test.md`,
`_config/package-and-layout.md`, `TESTING.md`, `RULES.md`,
`templates/test-intent-derivation-map.md`. Profile reference docs
(`reference-impl/<profile>/`) are loaded only when that profile is
selected.

## Process

1. **Derive `output/concept-test-derivation.md`** from the `04b` contracts
   using the derivation-map template: one row per (action × contract
   outcome), quoting the spec line for any outcome no scenario exercises,
   and naming the test class and method.
2. **Write the concept unit tests** under `APP_TEST_SOURCE_ROOT`. Every
   test asserts the `outcome` and the primary completion field values
   that downstream syncs consume.
3. **Implement each concept** so those tests pass. One public action
   emits exactly one flow token (R5); each contract outcome is a distinct
   branch (R9); concept code imports no other concept (R1).
4. **Write `output/verification-evidence.md`** recording the executed
   test command and result, contract-outcome coverage, and the mutation
   score when `mutation.command` is configured.

Self-audit: run `python3 quality-gate/verify_artefacts.py` before advancing.

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
`verify_concept_field_assertions.py` enforces this.

## Hard constraints

- Tests and implementation are produced together — implement nothing
  before its unit test exists (R8).
- One test class per concept action; one row per contract outcome.
- Every concept unit test asserts the outcome and the primary completion
  field values that downstream syncs consume.
- No cross-concept imports (R1).
- Every public action emits a flow token (R5).
- Distinct contract outcomes remain distinct in code paths (R9).
- Do not substitute an in-memory store for the configured storage layer.
- Use the exact package/source-root from `_config/package-and-layout.md`.
- Test effectiveness is the mutation score (`mutation.command` /
  `mutation.threshold`, checked by `verify_mutation_score.py`) — not a
  red-green ritual or a test count.

## Test naming (advisory)

CLAD recommends, but does not gate, these conventions for concept unit
tests (`verify_test_naming.py` reports drift, it does not block):

- **Class name:** `<Concept><Action>Test` (e.g. `UserLookupByUsernameTest`)
- **`@Nested` class:** `When<Precondition>` groups outcomes by required state
  (e.g. `WhenUserExists`, `WhenUserUnknown`)
- **Method name:** `should<Behavior>When<Condition>` uses business language
  (e.g. `shouldReturnUserId`, `shouldReturnNotFound`)
- **Assertions:** the `outcome` and the primary completion field values
  (R14/R16), not internal concept state
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
