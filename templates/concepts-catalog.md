<!-- Reference for the system-scope concept catalog. The catalog is GENERATED —
this file documents its columns and the intrinsic/extrinsic dependence
distinction; it is not a fill-in template. Regenerate with
`quality-gate/generate_concepts_catalog.py --write`. -->

# Concepts catalog — generated reference

The catalog lives at `features/_system/concepts-catalog.md` and is derived from
the canonical corpus at `features/_system/concepts/<Name>.concept.md`. It is
**never hand-maintained** — edit the corpus spec, then re-run the generator.
It answers one question quickly: *does the capability (or action) my use case
needs already exist?*

## Columns

| Column | Source |
|---|---|
| Concept | the corpus filename |
| Purpose | the spec's `purpose` stanza |
| Type params | the spec header `concept <Name> [TypeParams]` |
| Actions | the spec's `## Actions` (names only) |
| Introduced by | the spec's `introduced-by` provenance line |
| Used by | features whose Stage-02 output binds the concept (`concept-bindings.md`) or carries a proposal |
| Notes | derived flags (e.g. `stateless`) |

## Intrinsic vs extrinsic dependence

These are two different things, and the distinction is load-bearing:

- **Intrinsic dependence — there is none.** A concept never imports another
  concept's state, actions, or types (hard rule **R1**). This is what makes
  concepts independent and reusable; it is why they can be shared across use
  cases. Nothing in this catalog authorises a concept to reach into a neighbour.
- **Extrinsic dependence — app-specific, and reviewed.** In a given app, one
  concept may *require* another because nothing else is a suitable supplier
  (e.g. `Comment` requires `Post`). That is recorded in
  `features/_system/concept-dependence.md`,
  never in a concept spec, and it is a hand-reviewed purpose judgment — not
  derived from the sync graph, and not authored by Stage 03a.

Coordination between concepts is expressed only by syncs (Stage 03). The
catalog's *Used by* column is provenance, not coupling.

## Out of scope for the catalog

- Concept *anatomy* (state, actions, outcomes) — that lives in the corpus spec
  `features/_system/concepts/<Name>.concept.md`.
- Concept *implementation paths* — they live under `reference-impl/<profile>/`.
