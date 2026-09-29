# Stage 04d — Concept implementation

## Why this stage exists

Implement the business concepts the feature uses, and the unit tests that
constrain them. This is a **single stage**: tests and implementation are
produced together — there is no red/green sub-stage split. The tests are
derived from the already-approved Stage 04b contracts and the 04c
Acceptance Spec; they are verification, not design.

Test effectiveness is measured by **mutation score**, not by a red-green
ritual (see `methodology/implementation/TESTING.md`). A suite that passes
but kills few mutants does not constrain the code and fails this stage
when the profile configures `mutation.command`.

Concept isolation (R1) still holds: concept tests load no other concept
and run no sync. If a concept test fails here, the defect is in that
concept; if the flow tests fail later after these are green, the defect
is in a sync.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../04b_contract/output/` | 4 | The contract each concept action must satisfy |
| `../../02_concepts/output/concept-bindings.md` | 4 | Which canonical concepts this feature uses |
| `../../../../../features/_system/concepts/` | 4 | Canonical concept specs |
| `../../02_concepts/output/<Name>.concept.md` | 4 | NEW/EXTEND proposals not yet promoted |
| `../../03_syncs/output/` | 4 | Syncs that consume concept completion fields |
| `../04c_acceptance-tests/output/acceptance-spec.md` | 4 | What the native tests must ultimately make true |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Derivation-map template |
| `../../../../../methodology/implementation/TESTING.md` | 3 | Spec-driven verification discipline |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Completion-field / token rules |
| Skill: `clad-concept-impl` | 3 | Concept test + implementation reference |

## Process

1. **Derive `output/concept-test-derivation.md`** from the contract
   slices using `../../../../../templates/test-intent-derivation-map.md`.
   One row per (action × contract outcome); quote the spec line for any
   outcome no scenario exercises. Record the test class and method.
2. **Write the concept unit tests** under the configured
   `test.source.root`. Every test asserts the `outcome` and the primary
   completion field values the downstream syncs read (R14/R16) — an
   outcome-only assertion is insufficient.
3. **Implement each concept** so the tests pass. One public action emits
   exactly one flow token (R5); each contract outcome is a distinct
   branch (R9); concept code imports no other concept (R1).
4. **Write `output/verification-evidence.md`** recording: the executed
   test command and result, contract-outcome coverage, and the mutation
   score (when `mutation.command` is configured).
5. Run the canonical build-and-test command from
   `../../../_config/build-and-test.md`.

## Outputs

- `output/concept-test-derivation.md` — action × outcome → test row
- `output/verification-evidence.md` — test run + coverage + mutation score
- (Side effect:) concept unit tests and concept implementation under the
  profile's concept package

## Verify

### Automated checks

```
python3 ../../../../../quality-gate/verify_profile_paths.py \
  --feature ../../../
python3 ../../../../../quality-gate/verify_concept_test_derivation.py \
  --contract-dir ../04b_contract/output \
  --derivation output/concept-test-derivation.md \
  --test-source-root <APP_TEST_SOURCE_ROOT>
python3 ../../../../../quality-gate/verify_concept_field_assertions.py \
  --contract-dir ../04b_contract/output \
  --test-source-root <APP_TEST_SOURCE_ROOT>
python3 ../../../../../quality-gate/verify_mutation_score.py \
  --feature-root ../../.. --scope concepts
python3 ../../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected concept-test-derivation.md,verification-evidence.md
```

- **verify_concept_test_derivation.py:** every contract outcome has a
  derivation row and a matching test method.
- **verify_concept_field_assertions.py:** concept tests assert the
  primary completion fields, not only the outcome token.
- **verify_mutation_score.py:** the concept suite meets
  `mutation.threshold` (skips when `mutation.command` is unset).
- **verify_file_manifest.py:** `output/` contains exactly the expected
  files.

### Semantic checks

- Every concept this feature uses has an implementation and tests.
- Each contract outcome maps to a distinct implementation branch (R9).
- No concept imports another concept (R1).
- Completion fields consumed by syncs are non-null on success.

## Advancing

> Do not open the next stage's `CONTEXT.md` yourself. After this stage's
> `output/` is written, end your turn by running the gate-driven advance
> command, which runs this stage's checks, enforces stage ordering, and
> tells you the next step:
>
> ```
> ./clad advance
> ```
>
> (Long form: `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`.)
> The CLI wrapper auto-discovers the feature from `RESUME.md`.
>
> Treat its output as your next instruction. It advances you, stops you
> at a human gate, or returns you to this stage with the defects to fix.
> See AGENTS.md §2 principle 12 and
> `methodology/implementation/STAGES.md` §"Gate-driven advance".
