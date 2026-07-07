<!-- Iterative-change planning aid. Purpose: post-green change workflow per methodology/core/CLAD.md §P5. -->

# Artefact impact matrix — `<change-name>`

> Use this **before** starting an iterative change to an existing
> feature. For each artefact category, fill in whether it is touched
> and how. Anything in the "touched" column has to be re-derived from
> its predecessor stage; CLAD's reversibility depends on you not
> editing late-stage artefacts in isolation.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `<presentation | behavioural | structural>`
- **Earliest re-entry stage:** `<stage id and name>`
- **Change summary:** `<one sentence>`

| Artefact | Path | Touched? | How |
|---|---|---|---|
| Use case | `features/UC-XX/stages/01_usecase/output/usecase.md` | yes \| no | <what changes> |
| Concept(s) | `features/UC-XX/stages/02_concepts/output/*.concept.md` | yes \| no | <which concepts, what changes> |
| Sync(s) | `features/UC-XX/stages/03_syncs/output/*.sync.md` | yes \| no | <which syncs, what changes> |
| SPEC slices | `features/UC-XX/stages/04_implement/04b_spec/output/*.spec.md` | yes \| no | <which> |
| Flow tests | `features/UC-XX/stages/04_implement/04c_flow-tests/output/` | yes \| no | <which> |
| Concept tests | `features/UC-XX/stages/04_implement/04d_concept-tdd/04d_red-tests/output/` | yes \| no | <which> |
| Sync tests | `features/UC-XX/stages/04_implement/04e_sync-tdd/04e_red-tests/output/` | yes \| no | <which> |
| Production code | `reference-impl/<profile>/...` | yes \| no | <which classes> |
| Verification trace | `features/UC-XX/stages/05_verify/output/` | yes \| no | <which scenarios> |

## Re-derivation order

> List the stages you will re-run, in order. Anything earlier than
> the earliest "touched" stage is unaffected.

1. <stage>
2. <stage>
3. <stage>

## Notes

> Optional.
