# Stage 04d-red — Concept Test Derivation (red)

## Pre-condition (agent must verify before starting)

Run the following **before** writing any artefacts for this stage:

```
python3 ../../../../../../quality-gate/verify_stage_output.py \
  --feature ../../../../ \
  --required-stages 02,04b,04c
```

If this script exits with a non-zero status, stop immediately.
Required upstream stage outputs are missing — do not proceed.

## Why this stage exists

This is the **red half** of concept TDD. Its only job is to derive
executable concept tests from approved outer artefacts, run them red,
and hand a precise contract to `04d-green`. Making this a separate ICM
folder gives weaker models a hard boundary: no production code belongs
here.

**Feeds:**

- `output/concept-test-derivation.md` plus approved test files -> `04d-green`
- approved concept tests -> Stage 05 coverage trace

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../../02_concepts/output/` | 4 | Concept specs |
| `../../04b_spec/output/` | 4 | SPEC slices to compile against |
| `../../04c_flow-tests/output/` | 4 | Drives test derivation |
| `../../../../_config/build-and-test.md` | 3 | Canonical build/test command for red evidence |
| `../../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings |
| Skill: `clad-concept-tdd` | 3 | Concept TDD reference (see skills/ directory) |
| `../../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R5, R14, R16 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School derivation rules |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` (only when this profile is selected) | 3 | Profile conventions |

## Process

1. Derive concept tests from approved outer artefacts. Start with
   `04c_flow-tests/output/`, then add any required action/outcome pairs
   from `04b_spec/output/` that are not exercised by the flow tests.
2. Write the concept test file(s) only under `APP_TEST_SOURCE_ROOT`.
   Do not write or modify production implementation code in this stage.
3. After asserting each outcome token, assert the primary completion
  fields that `writeCompletion` writes and downstream syncs consume.
  Outcome-only tests are incomplete.
4. Run the canonical command from `../../../../_config/build-and-test.md`
   and confirm the result is true red: test compilation succeeds and the
   tests fail for behavioral reasons.
5. Record the derivation map and the red-to-green handoff bundle in
   `output/concept-test-derivation.md`: approved test files, exact
   package/class/method names, red evidence command, expected red
   outcome, and the next implementation target.
6. Record the derivation map and the handoff bundle. The automated
    gate (`verify_concept_test_derivation.py`) will confirm the tests
    cover all SPEC outcomes. No human approval is required at this
    boundary — the design was settled at 04c (Gate 3).

## Outputs

- `output/concept-test-derivation.md` — derivation map plus handoff bundle
- (Side effect:) `<Concept><Action>Test.java` (or profile equivalent) per concept action

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "concept-test-derivation.md"
python3 ../../../../../../quality-gate/verify_concept_test_derivation.py \
  --spec-dir ../../04b_spec/output \
  --derivation output/concept-test-derivation.md \
  --test-source-root <APP_TEST_SOURCE_ROOT>
python3 ../../../../../../quality-gate/verify_concept_field_assertions.py \
  --spec-dir ../../04b_spec/output \
  --test-source-root <APP_TEST_SOURCE_ROOT>
python3 ../../../../../../quality-gate/verify_test_naming.py \
  --test-source-root <APP_TEST_SOURCE_ROOT> \
  --scope concepts
```

- **verify_file_manifest.py:** `output/` contains exactly
  `concept-test-derivation.md`.
- **verify_concept_test_derivation.py:** every SPEC outcome has a matching
  test row in the derivation map; every named test method exists in the
  Java source; outcome names match verbatim.
- **verify_concept_field_assertions.py:** Java concept tests that assert
  an outcome also assert every required completion field from the SPEC
  flow-token shape.
- **verify_test_naming.py:** every concept test class follows London School
  naming conventions (class: `<Concept><Action>Test`, method prefix: `should`,
  `@Nested` groups present, `// GIVEN/WHEN/THEN` comments).

### Semantic checks (human)

- `output/concept-test-derivation.md` exists.
- Every test row traces back to an approved `04c` flow test or an
  approved `04b` SPEC outcome. No test case was invented without one of
  those sources.
- Every concept test asserts the outcome and the primary completion
  fields downstream syncs consume; no valid-input primary field assertion
  accepts null or empty string.
- Tests live under `APP_TEST_SOURCE_ROOT` and packages consistent with
  `APP_PACKAGE_ROOT`.
- Executed red evidence shows successful test compilation and
  behavioral test failure.
- No test depends on another concept's state or sync orchestration;
  those cases belong in `04e`.
- No production concept implementation was introduced or changed during
  this stage.
- The handoff bundle names the approved test files, exact
  package/class/method names, the red evidence command, expected red
  outcome, and the next implementation target.

## Gate

Auto-advances to 04d-green. Concept tests are mechanically derived
from approved artefacts (Gate 3 flow tests + 04b SPECs) — they verify
implementation fidelity, not settle design. The
`verify_concept_test_derivation.py` and `verify_file_manifest.py`
scripts must pass before advancing. If either fails, the agent stops
— the derivation does not match the SPEC outcomes or the expected
files are missing.

## Next stage

-> [`../04d_green-impl/CONTEXT.md`](../04d_green-impl/CONTEXT.md) — Implement approved concept tests only
