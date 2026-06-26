# Legible architecture (the WYSIWID pattern)

> **WYSIWID** — *What You See Is What It Does.* Reading a concept's
> specification tells you, with no further indirection, what the running
> system does when that concept is invoked.
>
> Adapted from Eagon Meng & Daniel Jackson, *What You See Is What It Does:
> A Structural Pattern for Legible Software*, Onward! 2025
> ([DOI 10.1145/3759429.3762628](https://doi.org/10.1145/3759429.3762628),
> [arXiv 2508.14511](https://arxiv.org/abs/2508.14511)). The original paper
> is the canonical source; this file is a working summary written for the
> CLAD seed.

## The pattern in one paragraph

A Legible system is decomposed into **concepts**: small, self-contained
state machines that each model one user-facing capability (authentication,
sessions, comments, notifications). Concepts know nothing about each
other. They are coordinated only by **synchronizations** — declarative
"when *X* completes, then *Y*" rules that live outside the concepts. A
single bootstrap concept (typically called `Web`) owns the system's HTTP
surface and translates external requests into concept actions. Every
action emits a **flow token**, a small addressable record that lets you
trace any runtime effect back to the request that caused it.

The pattern is "legible" because the things you read in the concept and
sync specs are the things the runtime does. There is no hidden
controller, no implicit framework magic, no cross-cutting middleware
that changes meaning. Provenance is structural, not best-effort.

## Why this matters for CLAD

CLAD's promise — that an AI agent can build software a human can still
audit — is empty without an architecture that makes the running system
auditable. Legible/WYSIWID is that architecture:

| CLAD wants… | Legible delivers it via… |
|---|---|
| Reviewable specs of behaviour | Concept specs (small, self-contained) |
| Localised changes | One concept changes without dragging others |
| Authorisation traceable to a use case | Flow tokens emitted by every action |
| Coordination logic in one place, declaratively | Synchronizations as `when … then …` |

## Three pieces

1. **Concepts.** See [`CONCEPTS.md`](CONCEPTS.md). Each concept has
   *state*, *actions*, and an *operational principle* (a one-paragraph
   story of how the concept is meant to be used).
2. **Synchronizations.** See
   [`SYNCHRONIZATIONS.md`](SYNCHRONIZATIONS.md). Declarative `when { }`
   / `where { }` / `then { }` rules that fire when concept actions
   complete; they invoke other concept actions. No business logic lives
   here, only wiring.
3. **Flow tokens.** See [`FLOW_TOKENS.md`](FLOW_TOKENS.md). Every
   action emits one; they are the breadcrumbs that make stage 5
   verification possible.

## What Legible is not

- It is not a framework. There is no Legible runtime to install.
- It is not an event bus. Synchronizations are not pub/sub messages;
  they are typed coordination rules.
- It is not microservices. Concepts can run in one process; their
  isolation is lexical and lifecycle-based, not network-based.
- It is not DDD bounded contexts. A concept is smaller than a
  bounded context and is defined by *user-facing capability*, not by
  team boundary.

## Hard constraints

These are restated, with examples, in
[`../implementation/RULES.md`](../implementation/RULES.md):

1. No concept imports or references another concept.
2. Concepts coordinate only through syncs.
3. Syncs are declarative, not branching.
4. `Web` is the only concept that owns the HTTP surface.
5. Every action emits a flow token.
