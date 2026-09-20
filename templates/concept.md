<!-- Template for Stage 02 (02_concepts). Purpose & authoring rules: methodology/architecture/CONCEPTS.md and the stage 02 CONTEXT "Process" section. This file is the output shape only.

Naming: name the capability (gerund/noun phrase — `Authentication`,
`Posting`), never the entity noun the set ranges over (`User`, `Post`).
State: subject is the *individual* (an identifier type, `UserId`), the
concept owns the *set*. See CONCEPTS.md §"State over a set, not fields of an object".

Actions: OUTCOME ALIGNMENT — every outcome name must match the approved
01b chain-table Outcome column verbatim. Never invent an outcome here;
if one is missing, reopen Stage 01b.

Provenance: `introduced-by <UC-XX-slug>` records the feature that first
introduced the concept. In a UC's Stage-02 output this is a PROPOSAL
(promoted to the corpus on gate approval); in the canonical corpus at
features/_system/concepts/ it is the provenance of record. Do not edit
it by hand in the corpus — promotion writes it. -->

concept <ConceptName> [<TypeParams>]
introduced-by <UC-XX-slug>
purpose
    <one-line capability statement>

## State

> The data this concept owns. No other concept may read or write it.
> Paper-style relational notation: `field: SubjectType -> FieldType  -- multiplicity`
> Multiplicity: `mandatory` | `optional` | `conditional mandatory: <condition>` | `zero or more`.
> Stateless concept: `*None.* <ConceptName> is stateless.`
> Separate views under one noun are separate capabilities — split them.

```
<fieldName>: <SubjectType> -> <FieldType>   -- mandatory
<fieldName>: <SubjectType> -> <FieldType>   -- optional
```

## Actions

<!-- OUTCOME ALIGNMENT: every output name below must match the approved
01b chain table Outcome column verbatim. If you need an outcome the chain
table did not name, reopen Stage 01b — do not invent outcomes here. -->

> The verbs this concept exposes. Each action is a local function call
> from a sync or from `Web`.
>
> **User actions vs system actions.** A *user action* is one an actor
> can invoke directly (surfaced through the bootstrap concept); a
> *system action* is invoked only by a sync — e.g. a lookup, or an
> action that only ever appears in a `then`. Both belong in this file.
> A sync may expose a single action (a `when`/`then` pair is a complete
> concept invocation), so do not invent a user action merely because a
> flow needs one.
>
> Two formats:
>
> **A. Precondition/postcondition** (failures are pure state-guard
> violations): precondition failure → refusal (`:outcome "refused"`), no
> state change; postcondition describes the happy-path transition.
> **B. Case-split outcomes** (failures still mutate state): each outcome
> is a named completion (`[ ok ]`, `[ error: "badPassword" ]`).

Format A — precondition/postcondition:

```
<actionName> [ <arg>: <Type> ; ... ] => [ <field>: <Type> ]
    precondition {
        <guard-1>
        <guard-2>
    }
    postcondition {
        <state-transition-assertion>
    }
    <description of effect on state>
    flow token: { action: "<ConceptName>.<actionName>", <args>, outcome: "<outcome>" }
```

Format B — case-split outcomes:

```
<actionName> [ <arg>: <Type> ; <arg2>: <Type> ] => [ <field>: <Type> ]
    <description of happy path and effect on state>
    flow token: { action: "<ConceptName>.<actionName>", <args>, outcome: "<outcome>" }

<actionName> [ <arg>: <Type> ; ... ] => [ error: "<errorName>" ]
    <condition under which this error fires>
```

## Operational principle

> A witness trace of the typical happy path, written in sync notation
> (`after`/`then`). This proves the actions compose correctly and serves
> as the WYSIWID heart of the spec. Happy path, one sequence, no branching —
> with one exception: a refusal that demonstrates the concept's invariant
> belongs here. Action names are fully qualified (concept prefix included)
> for direct traceability to sync specs.
>
> **Each step after the first must DEPEND on an earlier step's effect.** The
> notation reads as a sequence, so a step that is merely another independent
> call — enrolling a *second, unrelated* member; recording a *second,
> unrelated* title — is a fake sequence and proves nothing. When a concept has
> one action and no composition to show, witness the invariant its guard
> enforces instead: repeat the call with the same key and show the refusal
> (`then <ConceptName>/<action>: [ … ] => [ error: "duplicateKey" ]`).

```
after  <ConceptName>/<action>: [ <param>: <value> ] => [ <result>: <value> ]
then  <ConceptName>/<action>: [ <param>: <value> ] => [ <result>: <value> ]
```

## Notes

> Optional. Edge cases, invariants, open questions, or scope boundaries
> for the human reviewer.
