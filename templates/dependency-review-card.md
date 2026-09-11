<!-- Template for Stage 03a (03a_dependency-review). One file per concept. Purpose: see methodology/implementation/STAGES.md §"Stage 03a" and methodology/architecture/SYNC_PATTERNS.md. -->

# Dependency review — `<ConceptName>`

> Per-concept dependency card. One file per concept that appears in
> any chain table. The card answers two questions:
>
> 1. **Inbound calls** — which actions on this concept are invoked by
>    syncs, from which flows, with which data, and from what source?
> 2. **Inbound state reads** — which fields of this concept's named
>    region are read by *other* concepts' syncs (concept-state reads)?
>
> The card does **not** describe what this concept does internally —
> that is the concept spec's job (Stage 02). It describes only the
> concept's exposure to the rest of the system.
>
> A concept-state read is the only legal cross-concept data access; see
> `methodology/architecture/SYNC_PATTERNS.md` (relative path depends on
> where this card is materialised — typically
> `../../../../../methodology/architecture/SYNC_PATTERNS.md` from a
> stage `output/` folder).
>
> This card is an exact-token audit of the approved syncs. Copy action
> names, argument names, field names, source descriptions, keys, status
> codes, and literals exactly. Do not normalize casing, hyphenation, or
> numeric-vs-string form.

## Section 1 — Invocations received

> **Only `then` calls go here. `when` triggers do NOT.**
> A sync's `when` clause names the outcome that *fires* this sync — that
> is not an invocation of this concept. Only the sync's `then` clause
> *invokes* a concept action. If a sync has `when: Account.validate(...) -> Valid`
> and `then: Account.create(...)`, that sync contributes exactly one row
> here: under `create`, not under `validate`.
>
> One row per (sync × action) where the sync's `then` calls that action.
> The `Source` column describes where the action's arguments come from:
>
>   internal flow — argument from trigger input, sibling output, or a
>                  sync constant (all within the same flow token)
>   concept-state — argument from a named-region read of another concept

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `<actionName>` | `<SyncName>` (`<scenario>`) | `<arg1>, <arg2>` | `A`/`B`/`C` | `when.field` / `result_of(Other.action).bar` / literal `200` / `Other.field` |
| `<actionName>` | `<SyncName>` (`<scenario>`) | … | … | … |

> The `Pattern` column is the `SYNC_PATTERNS.md` data-flow label for how the
> argument reached this invocation: `A` (from the trigger token), `B` (from a
> prior action's output), or `C` (a sync constant). `D` is a concept-state
> read and belongs in Section 2, not here.

> **Example:** Given these two syncs:
>   Sync 1 — `when: Web.request -> Routed` / `then: Account.validate(email, password)`
>   Sync 2 — `when: Account.validate -> Valid` / `then: Account.create(email, password)`
>
> The Section 1 table for `Account` has exactly **2 rows**:
>   | `validate` | Sync 1 | email, password | body.email, body.password |
>   | `create`   | Sync 2 | email, password | result_of(Account.validate).email, … |
>
> Sync 2 does **not** produce a row for `validate` — `validate` is Sync 2's
> `when` trigger, not its `then` invocation.

> If the same action receives its arguments from **different sources in
> different flows**, that is almost always a defect — the data source
> disagrees across flows. Flag it in *Inconsistencies* below.
>
> If a row here would need to differ from the approved sync text, stop.
> The mismatch belongs in Stage 03 (or earlier), not in this review card.

## Section 2 — Named-region reads by others (inbound concept-state reads)

> Every row is one concept-state read of *this concept's* named region by
> some *other* concept's sync. If this list is non-empty, this
> concept is being treated as a value source by the system; that
> coupling is now visible.

| Field | Read by (sync) | In flow | Key |
|---|---|---|---|
| `<fieldName>` | `<SyncName>` | `<scenario>` | `<id>` |
| `<fieldName>` | `<SyncName>` | `<scenario>` | `<id>` |

> If this list is empty, write *"None — no other concept reads this
> concept's named region."* Do not delete the section; the empty
> assertion is the point.

## Inconsistencies and risks

> Optional. List any of:
>
> - Same action receives data from different sources in different flows.
> - Same field read as concept-state in some flows but reconstructed from
>   internal flow data in others.
> - A field exposed to many other concepts (suggests it should be
>   modelled as its own concept, or moved).

- <inconsistency, or "none">

## Cross-checks

- Every `Action` row exists in this concept's `<ConceptName>.concept.md`.
- Every `Sync` named here exists in `../../03_syncs/output/`.
- Every concept-state read `Field` row appears in this concept's `state` section.
- Every copied token matches the approved sync text exactly.

---

**Do you agree with this card? Any corrections before I continue?**
