# Stage 04d-green — Concept Implementation (green)

## Pre-condition (agent must verify before starting)

Run the following **before** writing any implementation code:

```
python3 ../../../../../../quality-gate/verify_stage_sequence.py \
   --feature ../../../../ \
   --through 04d-red
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
| `../../../../../../reference-impl/java-legible/README.md` and `../../../../../../reference-impl/legible-engine/README.md` (default profile) | 3 | Profile conventions for the canonical fire-after-commit profile |
| `../../../../../../reference-impl/java-micronaut-jena/README.md`, `CODE_STYLE.md`, `CANONICAL_EXEMPLAR.md`, `SYNC_LOWERING.md` (legacy profile only) | 3 | Legacy RDF/SPARQL profile: ConceptAgent/SyncAgent lowering patterns. Do NOT follow when targeting java-legible |

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
   mapping when applicable, and the approved red tests. For the default
   profile (`java-legible`), a concept is a `Concept` implementation whose
   state lives in its own `Region` and whose actions are map→map (see
   `legible-engine/README.md`); the exemplar (`dev/legible/example/login`)
   is a realization pattern only and must not override the feature's
   approved artefacts. The `java-micronaut-jena` profile is legacy: consult
   its docs only when that profile was explicitly selected in Stage 04a.
5. Place concept code in the canonical concept package bucket (for the
   default profile: one `*Concept` class implementing `Concept` under
   `<APP_PACKAGE_ROOT>.concepts.<name>`, with tests mirrored under the
   corresponding test package). Do not place concept classes in
   `engine`, `syncs`, `infrastructure`, or ad hoc sibling packages.
6. Use the storage mapping from `04a_storage-mapping/output/` when applicable. Do not
   replace the selected profile's storage layer with an in-memory
   substitute.
7. Run the canonical command from `../../../../_config/build-and-test.md`
   until concept tests are green, then record the command and result in
   `output/green-evidence.md`.

## Outputs

- `output/green-evidence.md` — executed green command, result, and implementation files changed
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
- Concept classes are under `<APP_PACKAGE_ROOT>.concepts.<name>` and not
   in `engine`, `infrastructure`, `api`, `syncs`, or ad hoc sibling packages.

## Gate

Auto-advances to 04e-red. The concept tests must be green before advancing.

## Next stage

-> [`../../04e_sync-tdd/04e_red-tests/CONTEXT.md`](../../04e_sync-tdd/04e_red-tests/CONTEXT.md) — Sync test derivation (red)

The agent proceeds without a human gate.
