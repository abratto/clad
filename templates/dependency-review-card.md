<!-- Template for Stage 03a (03a_dependency-review). One file per concept. Purpose: see methodology/implementation/STAGES.md §"Stage 03a" and methodology/architecture/SYNC_PATTERNS.md. -->

# Dependency review — `<ConceptName>`

> Per-concept dependency card. One file per concept that appears in
> any chain table. The card answers two questions:
>
> 1. **Inbound calls** — which actions on this concept are invoked by
>    syncs, from which flows, with which data, joined via which
>    pattern (A/B/C/D), and from which source?
> 2. **Inbound state reads** — which fields of this concept's named
>    region are read by *other* concepts' syncs (Pattern D)?
>
> The card does **not** describe what this concept does internally —
> that is the concept spec's job (Stage 02). It describes only the
> concept's exposure to the rest of the system.
>
> Pattern D is the only legal cross-concept read; see
> [`../../../../methodology/architecture/SYNC_PATTERNS.md`](../../../../methodology/architecture/SYNC_PATTERNS.md).

## Section 1 — Invocations received

> Every row is one sync's `then` call into an action on this concept.
> Group by action; one row per (sync × flow × call). The `Source`
> column names where the call's argument data came from.

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `<actionName>` | `<SyncName>` (`<scenario>`) | `<arg1>, <arg2>` | A / B / C / D | `Web.handle.body.foo` / `result_of(Other.action).bar` / literal `"FOO"` / `Other.namedRegion.field` |
| `<actionName>` | `<SyncName>` (`<scenario>`) | … | … | … |

> If the same action is called via **different patterns in different
> flows**, that is almost always a defect — the data source disagrees
> across flows. Flag it in *Inconsistencies* below.

## Section 2 — Named-region reads by others (inbound Pattern D)

> Every row is one Pattern D read of *this concept's* named region by
> some *other* concept's sync. If this list is non-empty, this
> concept is being treated as a value source by the system; that
> coupling is now visible.

| Field | Read by (sync) | In flow | Pattern | Key |
|---|---|---|---|---|
| `<fieldName>` | `<SyncName>` | `<scenario>` | D | `<id>` |
| `<fieldName>` | `<SyncName>` | `<scenario>` | D | `<id>` |

> If this list is empty, write *"None — no other concept reads this
> concept's named region."* Do not delete the section; the empty
> assertion is the point.

## Inconsistencies and risks

> Optional. List any of:
>
> - Same action called via different patterns in different flows.
> - Same field read via Pattern D in some flows and reconstructed
>   via Pattern A/B in others.
> - A field exposed to many other concepts (suggests it should be
>   modelled as its own concept, or moved).

- <inconsistency, or "none">

## Cross-checks

- Every `Action` row exists in this concept's `<ConceptName>.concept.md`.
- Every `Sync` named here exists in `../../03_syncs/output/`.
- Every Pattern D `Field` row appears in this concept's `state` section.

---

**Do you agree with this card? Any corrections before I continue?**
