# Stage 04d-red — Concept Test Derivation (red)

## Pre-condition (agent must verify before starting)

**`../../04c_flow-tests/output/` must be non-empty.** If it is empty,
stop immediately and tell the human that Stage 04c must be completed and
gated before `04d-red` can begin.

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
| `../../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R5 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School derivation rules |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` (only when this profile is selected) | 3 | Profile conventions |

## Process

1. Derive concept tests from approved outer artefacts. Start with
   `04c_flow-tests/output/`, then add any required action/outcome pairs
   from `04b_spec/output/` that are not exercised by the flow tests.
2. Write the concept test file(s) only under `APP_TEST_SOURCE_ROOT`.
   Do not write or modify production implementation code in this stage.
3. Run the canonical command from `../../../../_config/build-and-test.md`
   and confirm the result is true red: test compilation succeeds and the
   tests fail for behavioral reasons.
4. Record the derivation map and the red-to-green handoff bundle in
   `output/concept-test-derivation.md`: approved test files, exact
   package/class/method names, red evidence command, expected red
   outcome, and the next implementation target.
5. Stop and present the red tests for human approval.

## Outputs

- `output/concept-test-derivation.md` — derivation map plus handoff bundle
- (Side effect:) `<Name>ConceptTest.java` (or profile equivalent) per concept

## Verify

### Gate progression pre-flight

Before any work, verify that the previous gate (if any) was approved:

```
python3 ../../../../../../quality-gate/verify_gate_progression.py \
  --current-stage 04_implement/04d_concept-tdd/04d_red-tests \
  --resume-feature ../../../../RESUME.md
```

- **verify_gate_progression.py:** ensures human gates are not skipped
  during auto-advance. If a preceding gate is missing approval, the
  script fails — the agent must present for review before continuing.


### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "concept-test-derivation.md"
python3 ../../../../quality-gate/verify_concept_test_derivation.py \
  --spec-dir ../../04b_spec/output \
  --derivation output/concept-test-derivation.md \
  --test-source-root ../../../../../../app/backend/src/test/java
```

- **verify_file_manifest.py:** `output/` contains exactly
  `concept-test-derivation.md`.
- **verify_concept_test_derivation.py:** every SPEC outcome has a matching
  test row in the derivation map; every named test method exists in the
  Java source; outcome names match verbatim.

### Semantic checks (human)

- `output/concept-test-derivation.md` exists.
- Every test row traces back to an approved `04c` flow test or an
  approved `04b` SPEC outcome. No test case was invented without one of
  those sources.
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

TDD phase approval. The `verify_concept_test_derivation.py` and
`verify_file_manifest.py` scripts must pass before requesting approval.
Then stop and wait for explicit human approval of the red tests before
starting `04d-green`. If either script fails, the agent stops — the
derivation does not match the SPEC outcomes or the expected files are
missing.

## Next stage

-> [`../04d_green-impl/CONTEXT.md`](../04d_green-impl/CONTEXT.md) — Implement approved concept tests only

The agent proceeds to 04d-green only after explicit human approval.
