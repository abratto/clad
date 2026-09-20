<!-- Template for Stage 01a (01a_responsibility-map). Purpose: see methodology/architecture/CONCEPTS.md and methodology/implementation/STAGES.md §"Stage 01a". -->

# Responsibility map — `<feature-name>`

> One row per concept the feature requires. The map answers
> *"which concepts exist and what does each own?"* — **not** how they
> are wired together (that is Stage 01b) and **not** what their
> internal anatomy is (that is Stage 02 itself, in `*.concept.md`).
>
> Keep this file flat and readable in one screen. If a row is
> ballooning, the concept is probably doing too much; split it.

## Derivation rubric

> Before writing the final Concepts table, derive candidate concepts
> from the approved use-case responsibilities. Use one row per distinct
> responsibility cluster or extension branch that might justify a
> separate concept. If two rubric rows collapse to the same capability
> owner, merge them in the final Concepts table.

| Use-case responsibility / branch | Candidate concept | Why this capability is separate | Why not the bootstrap concept? | Why not another listed concept? |
|---|---|---|---|---|
| `<scenario step or extension>` | `<Name>` | `<single capability in one verb phrase>` | `<why this is not just route / request / respond>` | `<why this is not owned by an already-listed concept>` |

> **Concept extraction tests.** A candidate concept survives into the
> final Concepts table only if it passes all of these:
>
> - **Capability test:** you can name its purpose in one short verb
>   phrase.
> - **Independence test:** you can specify its state and actions without
>   naming another concept's state or internals.
> - **Non-bootstrap test:** if it only routes, accepts transport input,
>   or emits transport output, it belongs in the bootstrap concept.
> - **Non-duplication test:** if an existing concept can own the same
>   responsibility without gaining a second unrelated purpose, reuse that
>   concept instead of creating a new one.

## Concepts

> **Consult the system vocabulary BEFORE deriving.** Read
> `features/_system/concepts-catalog.md` (the generated index — does the
> action I need already exist?) and `features/_system/concept-dependence.md`
> (the app-level extrinsic graph). Classify each concept's `Origin`:
>
> - `reused:UC-XX` — the concept and the actions needed already exist
>   canonically. Bind only; do NOT re-author the spec.
> - `extends:UC-XX` — the concept exists but the needed action/state does
>   not. Record a proposal below.
> - `new` — otherwise. Record a proposal below.
>
> `UC-XX` is the `introduced-by` provenance from the catalog. When the
> catalog and dependence graph do not yet exist (a project's first feature),
> every row is `new`.

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Web` | `new` | route table | `request`, `respond` | Bootstrap concept — see `methodology/architecture/WEB_CONCEPT.md`. Replace with `Grpc`, `Stream`, `Cli`, etc. if this feature's transport is not HTTP. |
| `<Name>` | `new` \| `reused:UC-XX` \| `extends:UC-XX` | `<field>: <Type>`, `<field>: <Type>` | `<actionName>`, `<actionName>` | <e.g. "no persistence in v1"> |
| `<Name>` | … | … | … | |

> **Bootstrap concept rule:** every feature must have exactly one
> bootstrap concept row — the concept that owns the transport boundary
> (entry point + exit point). For HTTP this is `Web`. Remove this
> comment block once the row is confirmed.

## Proposals

> One row for every concept whose Origin is `new` or `extends:UC-XX`.
> `reused:UC-XX` rows have NO row here — they bind to the canonical spec
> unchanged. Stage 02 authors each proposal to full anatomy in this
> feature's output; on gate approval it is promoted into the corpus with
> `./clad promote-concepts`. If a proposed `extends` would give the concept
> a second purpose, split it into a `new` concept instead.

| Concept | Kind | Proposed addition (actions / state) | Requires (dependence claim) | Rationale |
|---|---|---|---|---|
| `<Name>` | `new` \| `extends:UC-XX` | `<actionName>`, `<field>: <Type>` | `<ConceptName>` (or `—`) | <why the vocabulary must grow> |

> **Dependence claims are proposals, not edits.** `Requires` records what
> this concept would need present in *this app* (an extrinsic dependence —
> see `concept-dependence.md`). It is reviewed with the proposal at this
> feature's gate; the app-level graph is updated only through promotion.

## Coverage check

> For each scenario in `../01_usecase/output/usecase.md`, list the
> concepts that participate. Every scenario must touch at least one
> concept; every concept must be touched by at least one scenario.
> List every extension scenario as its own row.

| Scenario | Concepts touched |
|---|---|
| `<main-scenario-name>` | `Web`, `<Name>` |
| `<main-scenario-name> ext <Xa> — <label>` | `Web`, `<Name>` |

## Out of scope

> Things you considered making concepts but rejected (with one-line
> reason). This is the Stage 02 equivalent of the use case's
> "Out of scope" — keeps later reviewers from re-litigating.

- `<RejectedName>` — <reason>
