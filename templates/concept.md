<!-- Template for Stage 02 (02_concepts). Purpose & authoring rules: methodology/architecture/CONCEPTS.md and the stage 02 CONTEXT "Process" section. This file is the output shape only.

Naming: name the capability (gerund/noun phrase — `Authentication`,
`Posting`), never the entity noun the set ranges over (`User`, `Post`).
State: subject is the *individual* (an identifier type, `UserId`), the
concept owns the *set*. See CONCEPTS.md §"State over a set, not fields of an object".

Actions: OUTCOME ALIGNMENT — every outcome name must match the approved
01b chain-table Outcome column verbatim. Never invent an outcome here;
if one is missing, reopen Stage 01b. -->

concept <ConceptName> [<TypeParams>]
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
> from a sync or from `Web`. Two formats:
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
> as the WYSIWID heart of the spec. Happy path only — one sequence,
> no branching. Action names are fully qualified (concept prefix included)
> for direct traceability to sync specs.

```
after  <ConceptName>/<action>: [ <param>: <value> ] => [ <result>: <value> ]
then  <ConceptName>/<action>: [ <param>: <value> ] => [ <result>: <value> ]
```

## Notes

> Optional. Edge cases, invariants, open questions, or scope boundaries
> for the human reviewer.
