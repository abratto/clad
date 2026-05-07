<!-- Template for Stage 02a (02a_responsibility-map). Purpose: see methodology/architecture/CONCEPTS.md and methodology/implementation/STAGES.md §"Stage 02a". -->

# Responsibility map — `<feature-name>`

> One row per concept the feature requires. The map answers
> *"which concepts exist and what does each own?"* — **not** how they
> are wired together (that is Stage 02b) and **not** what their
> internal anatomy is (that is Stage 02 itself, in `*.concept.md`).
>
> Keep this file flat and readable in one screen. If a row is
> ballooning, the concept is probably doing too much; split it.

## Concepts

| Concept | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|
| `<Name>` | `<field>: <Type>`, `<field>: <Type>` | `<actionName>`, `<actionName>` | <e.g. "no persistence in v1"> |
| `<Name>` | … | … | |

## Coverage check

> For each scenario in `../01_usecase/output/usecase.md`, list the
> concepts that participate. Every scenario must touch at least one
> concept; every concept must be touched by at least one scenario.

| Scenario | Concepts touched |
|---|---|
| `<scenario-name>` | `<Name>`, `<Name>` |

## Out of scope

> Things you considered making concepts but rejected (with one-line
> reason). This is the Stage 02 equivalent of the use case's
> "Out of scope" — keeps later reviewers from re-litigating.

- `<RejectedName>` — <reason>
