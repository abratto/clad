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

| Artefact | Touched? | How |
|---|---|---|
| Use case | `yes` / `no` | <what changes> |
| Concept(s) | `yes` / `no` | <which concepts, what changes — corpus and/or proposal> |
| Sync(s) | `yes` / `no` | <which syncs, what changes> |
| Contract slices | `yes` / `no` | <which> |
| Flow tests | `yes` / `no` | <which scenarios in `acceptance-spec.md` / which native flow tests> |
| Concept tests | `yes` / `no` | <which concept unit tests> |
| Sync tests | `yes` / `no` | <which sync unit tests> |
| Production code | `yes` / `no` | <which classes> |
| Verification trace | `yes` / `no` | <which scenarios> |

## Re-derivation order

> List the stages you will re-run, in order. Anything earlier than
> the earliest "touched" stage is unaffected.

1. <stage>
2. <stage>
3. <stage>

## Notes

> Optional.
