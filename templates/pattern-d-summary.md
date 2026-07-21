<!-- Template for Stage 03a (03a_dependency-review). One file per feature, summarising every concept-state read across all flows. Purpose: see methodology/implementation/STAGES.md §"Stage 03a" and methodology/architecture/SYNC_PATTERNS.md. -->

# Concept-state reads — UC-XX

> Consolidated cross-flow view of every **concept-state read** in this
> feature — i.e. every place where a sync reads from a concept's
> named region. This is the feature's complete cross-concept-coupling
> surface.
>
> If a row appears here, the consumer concept depends on the owner
> concept's stored state. If a row should appear here but the data is
> currently being obtained from internal flow data in some flow, that
> is a flow inconsistency — call it out.
>
> This summary is token-locked to the approved sync pack. Copy sync
> names, owner concept names, field names, keys, and literals exactly.
> If you find a mismatch, surface it as a defect; do not normalize it.

## Concept-state reads

| Consumer (sync) | Field read | Owner concept | Key | In flow |
|---|---|---|---|---|
| `<SyncName>` | `<field>` | `<OwnerConcept>` | `<id>` | `<scenario>` |
| `<SyncName>` | `<field>` | `<OwnerConcept>` | `<id>` | `<scenario>` |

> If empty, write *"No concept-state reads in this feature."* The empty
> assertion is the artefact.

## Cross-flow inconsistencies

> Same field read as concept-state in some flows but obtained from
> internal flow data in others; same field with different keys; etc.
>
> Also record any exact-token drift discovered here: renamed fields,
> recased literals, quoted numeric status codes, or key-name drift.

- <inconsistency, or "none">

## What this feeds

- **Stage 03b (data model).** The owner concept's data model must
  include every field listed in the *Field read* column.
- **Stage 04a (storage mapping).** The owner concept's storage mapping
  must realize those approved fields in the selected profile.
- **Stage 04b (spec).** The consumer sync's spec must name the owner
  concept and the field by the same names used here.
- **Stage 05 (verify).** Each row is a runtime trace target — the
  flow test for the named scenario must exercise this read.

---

**Do you agree with this summary? Any corrections before I continue?**
