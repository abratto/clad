# Stage 04d-green — Concept Implementation (green)

## Pre-condition (agent must verify before starting)

Run the following **before** writing any implementation code:

```
python3 ../../../../../../quality-gate/verify_stage_output.py \
  --feature ../../../../ \
  --required-stages 04d
```

If this script exits with a non-zero status, stop immediately.
Stage 04d-red concept test derivation is missing — do not implement
before tests are derived.

## Why this stage exists

This is the **green half** of concept TDD. Its only job is to implement
exactly what the approved red tests require. Making this a separate ICM
folder gives weaker models a hard boundary: implementation may consult
upstream prose, but it may not redesign approved tests.

**Feeds:**

- green concept implementation -> `04e`
- green concept tests -> Stage 05 traceability

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../../02_concepts/output/` | 4 | Concept specs |
| `../../04a_storage-mapping/output/` | 4 | Storage mapping when a persistent profile applies |
| `../../04b_spec/output/` | 4 | SPEC slices to preserve outcome distinctions |
| `../04d_red-tests/output/` | 4 | Approved red tests and handoff bundle |
| `../../../../_config/build-and-test.md` | 3 | Canonical build/test command for green evidence |
| `../../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings |
| Skill: `clad-concept-tdd` | 3 | Concept TDD reference (see skills/ directory) |
| `../../../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R5, R8, R9, R14, R16 |
| `../../../../../../methodology/implementation/TDD.md` | 3 | London School handoff semantics |
| `../../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` (only when this profile is selected) | 3 | Profile conventions |
| `../../../../../../reference-impl/java-micronaut-jena/CANONICAL_EXEMPLAR.md` (only when this profile is selected) | 3 | Profile realization pattern, not source of truth |
| `../../../../../../reference-impl/java-micronaut-jena/SYNC_LOWERING.md` (only when this profile is selected) | 3 | Concept SPARQL patterns: SELECT, UPDATE, writeCompletion, test fixtures |

## Process

1. Read the approved red tests and the handoff bundle from
   `../04d_red-tests/output/`.
2. Extract and match exactly: package declarations, class names, method
   signatures, referenced inner types, and test expectations.
3. Implement only what is needed to make the approved concept tests
   pass. Do not redesign the tests during this stage. If they appear
   wrong or incomplete, stop and send the work back to `04d-red` or the
   earliest invalid upstream stage.
4. Derive behavior from the approved upstream artefacts first: the
   Stage 02 concept spec, the `04b` SPEC slice, the `04a` storage
   mapping when applicable, and the approved red tests. If the selected
   profile is Java/Jena/Micronaut, use `CANONICAL_EXEMPLAR.md` only as a
   realization pattern for class/package/code shape. It must not
   override the feature's own approved artefacts.
5. If the selected profile is Java/Jena/Micronaut, place concept code in
   the canonical concept package bucket: one `*Concept` class under
   `<APP_PACKAGE_ROOT>.concepts.<name>`, with its tests mirrored under
   the corresponding test package. Do not place concept agents in
   `engine`, `syncs`, `infrastructure`, or ad hoc sibling packages.
6. Use the storage mapping from `04a_storage-mapping/output/` when applicable. Do not
   replace the selected profile's storage layer with an in-memory
   substitute.
7. Run the canonical command from `../../../../_config/build-and-test.md`
   until concept tests are green, then stop for human approval.

## Outputs

- (Side effect:) `<Name>Concept.java` and green `<Name>ConceptTest.java` files (or profile equivalents) per concept

## Verify

- All approved concept tests are green.
- Run `quality-gate/verify_iterative_change_coupling.py` before merge when
   concept implementation changed; matching Stage 02 concept artefacts must be
   in the same diff.
- Green tests include assertions for primary completion field values,
  not only outcome tokens.
- Every required concept test and implementation file exists in the
  selected profile's source tree.
- Behavior is traceable first to the approved upstream artefacts; any
   profile exemplar was used only as a realization pattern.
- Green implementation treated the approved red tests as the immediate
  contract and did not reinterpret earlier artefacts against them.
- No cross-concept imports.
- Every public concept action emits a flow token.
- Distinct SPEC outcomes remain distinct in code paths; no approved
  outcomes were collapsed.
- Implementation package/source path matches
  `../../../../_config/package-and-layout.md` (`APP_PACKAGE_ROOT`,
  `APP_SOURCE_ROOT`, `APP_TEST_SOURCE_ROOT`).
- For the Java/Jena/Micronaut profile, concept classes are under
   `<APP_PACKAGE_ROOT>.concepts.<name>` and not in `engine`,
   `infrastructure`, `api`, `syncs`, or ad hoc sibling packages.

## Gate

Auto-advances to 04e. The concept tests must be green
(`mvn test`) before advancing.

## Next stage

-> [`../../04e_sync-tdd/CONTEXT.md`](../../04e_sync-tdd/CONTEXT.md) — Sync TDD router

The agent proceeds to Stage 04e without a human gate.
