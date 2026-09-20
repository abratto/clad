<!-- Template for Stage 02 (02_concepts). This file is ALWAYS emitted, even when
every concept is reused — a feature may reuse the whole vocabulary and propose
nothing. Purpose & rules: 02_concepts/CONTEXT.md and
methodology/architecture/CONCEPTS.md. This file is the output shape only. -->

# Concept bindings — `<feature-name>`

> One row per concept this feature uses (bootstrap transport concepts are
> governed separately and are not listed). `Origin` mirrors the Stage-01a
> responsibility map:
>
> - `reused:UC-XX` — bound to the canonical corpus spec, unchanged. There is
>   **no** `<Name>.concept.md` in this feature's Stage-02 output.
> - `extends:UC-XX` — the canonical concept exists; this feature emits a
>   PROPOSAL `<Name>.concept.md` adding the actions/state it needs.
> - `new` — no canonical concept; this feature emits a PROPOSAL
>   `<Name>.concept.md`.
>
> `UC-XX` is the concept's `introduced-by` provenance (see
> `_system/concepts-catalog.md`). Proposals are promoted into the corpus only
> on gate approval (`./clad promote-concepts`).

| Concept | Origin | Actions used | Proposal |
|---|---|---|---|
| `<Name>` | `reused:UC-XX` | `<actionName>`, `<actionName>` | — |
| `<Name>` | `new` \| `extends:UC-XX` | `<actionName>` | `<Name>.concept.md` |

## Notes

> Optional. Cross-feature coordination this feature relies on, or open
> questions about an existing concept's contract.
