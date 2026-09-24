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

> **A project's corpus starts empty.** CLAD seeds no concepts: an app's domain
> is not known in advance. The corpus grows only from *this* project's features
> (promoted on Gate 2 approval), so the graph below begins with no edges. See
> the completed example at
> [`../../examples/UC-00-login/`](../../examples/UC-00-login/) for what a filled
> graph looks like.

## How to read an edge

An edge `A → B` ("A requires B") means: in this app, `A` cannot function
unless `B` is present, because `B` is the only suitable supplier of something
`A` needs (usually an identifier type). A missing supplier is a design gap, not
a wiring detail — resolve it here before scheduling.

## Edges

| Concept | requires | Why (extrinsic, app-specific) |
|---|---|---|
| *(none yet)* | — | Promote a feature's concepts (Gate 2) and record the edges this project depends on. |

## Topological levels (implementation schedule)

- *(none yet)*

Levels are the parallel-work units (D7). Concepts in the same level share no
edge and may be authored concurrently.

## Valid subsets

Every app is a subset of the vocabulary plus its edges. A subset is **coherent**
when it is closed under `requires` (every concept's suppliers are present).
With an empty corpus there is nothing to schedule yet; the graph fills in as
concepts are promoted.

## Provenance

The canonical specs live in [`concepts/`](concepts/); the generated index is
[`concepts-catalog.md`](concepts-catalog.md). This project's corpus starts
empty and is seeded only by its own promoted features.
