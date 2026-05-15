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
> `methodology/architecture/SYNC_PATTERNS.md` (relative path depends on
> where this card is materialised — typically
> `../../../../../methodology/architecture/SYNC_PATTERNS.md` from a
> stage `output/` folder).
>
> This card is an exact-token audit of the approved syncs. Copy action
> names, argument names, field names, pattern labels, keys, status codes,
> and literals exactly. Do not normalize casing, hyphenation, or
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
> The `Pattern` and `Source` columns describe how the *arguments* to that
> `then` call were obtained (from the sync's `where` clause).
>
> Pattern reference:
>   A — argument comes from Web.handle body (flow-token join)
>   B — argument comes from a prior action's output (flow-sibling join)
>   C — argument is a sync constant (literal)
>   D — argument is a named-region read from another concept's state

| Action | Flow (sync) | Data received | Pattern | Source |
|---|---|---|---|---|
| `<actionName>` | `<SyncName>` (`<scenario>`) | `<arg1>, <arg2>` | A / B / C / D | `Web.handle.body.foo` / `result_of(Other.action).bar` / literal `"FOO"` / `Other.namedRegion.field` |
| `<actionName>` | `<SyncName>` (`<scenario>`) | … | … | … |

> **Example:** Given these two syncs:
>   Sync 1 — `when: Web.handle -> Routed` / `then: Account.validate(email, password)`
>   Sync 2 — `when: Account.validate -> Valid` / `then: Account.create(email, password)`
>
> The Section 1 table for `Account` has exactly **2 rows**:
>   | `validate` | Sync 1 | email, password | A | body.email, body.password |
>   | `create`   | Sync 2 | email, password | B | result_of(Account.validate).email, … |
>
> Sync 2 does **not** produce a row for `validate` — `validate` is Sync 2's
> `when` trigger, not its `then` invocation.

> If the same action is called via **different patterns in different
> flows**, that is almost always a defect — the data source disagrees
> across flows. Flag it in *Inconsistencies* below.
>
> If a row here would need to differ from the approved sync text, stop.
> The mismatch belongs in Stage 03 (or earlier), not in this review card.

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
- Every copied token matches the approved sync text exactly.

---

**Do you agree with this card? Any corrections before I continue?**
