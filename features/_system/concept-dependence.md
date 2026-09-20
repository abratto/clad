# Concept dependence — `<project name>`

> **App-level EXTRINSIC dependence graph** (maintenance change
> `system-scope-concept-vocabulary`, decision D4). This file is **reviewed by
> hand**, not generated: it records the purpose judgment "in *this* app, A
> requires B because nothing else is a suitable supplier".
>
> It is **not** intrinsic dependence. Concepts never import one another (R1);
> there are no intrinsic dependencies. Nor is it derived from the sync graph or
> from the Stage 03a coordination cards — those are *evidence* for a possible
> edge, never its source (D10). It is a product-design statement.
>
> It serves as the **implementation scheduling graph**: concepts in the same
> topological level have no dependence edges between them and may be built in
> parallel (D7).

## How to read an edge

An edge `A → B` ("A requires B") means: in this app, `A` cannot function
unless `B` is present, because `B` is the only suitable supplier of something
`A` needs (usually an identifier type). A missing supplier is a design gap, not
a wiring detail — resolve it here before scheduling.

## Edges

| Concept | requires | Why (extrinsic, app-specific) |
|---|---|---|
| `UserNaming` | — | Root: it mints the opaque `UserId` other concepts key on. |
| `PasswordAuth` | `UserNaming` | Its currency is `UserId`; in this app the only supplier of a `UserId` is `UserNaming`. |
| `Session` | `UserNaming` | A session records a principal as a `UserId`; supplied only by `UserNaming`. |

`Session` does **not** require `PasswordAuth`. A session merely records that an
authentication happened; it is coherent without `PasswordAuth`. The
"authenticate, then grant" sequencing of a login is **coordination**, expressed
by a sync — not a dependence. This is the canonical example of why 03a cards
are evidence for an edge rather than its source.

## Topological levels (implementation schedule)

- **Level 0:** `UserNaming`
- **Level 1:** `PasswordAuth`, `Session`

Levels are the parallel-work units (D7). `PasswordAuth` and `Session` share no
edge and may be authored concurrently once `UserNaming` is canonical.

## Valid subsets

Every app is a subset of the vocabulary plus its edges. A subset is **coherent**
when it is closed under `requires` (every concept's suppliers are present).

| Subset | Concepts | Coherent? | Rationale |
|---|---|---|---|
| Naming only | `UserNaming` | yes | Root concept stands alone. |
| Naming + auth | `UserNaming`, `PasswordAuth` | yes | Authentication without sessions. |
| Naming + session | `UserNaming`, `Session` | yes | Anonymous/attributed sessions. |
| Login app | `UserNaming`, `PasswordAuth`, `Session` | yes | The worked example `UC-00-login`. |

A subset that contains `PasswordAuth` or `Session` but **not** `UserNaming` is
incoherent — its supplier is missing. Because this graph is reviewed (not
derived), coherence is judged by the human at corpus acceptance; the promotion
receipt records any pending dependence claims for that review.

## Provenance

Seeded from the `UC-00-login` worked example's three concepts
(`UserNaming`, `PasswordAuth`, `Session`). Per D2 the canonical specs live in
[`concepts/`](concepts/); the generated index is
[`concepts-catalog.md`](concepts-catalog.md).
