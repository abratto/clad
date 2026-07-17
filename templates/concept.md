<!-- Template for Stage 02 (02_concepts). Purpose: see methodology/architecture/CONCEPTS.md. -->

concept <ConceptName> [<TypeParams>]
purpose
    <one-line capability statement>

## State

> The data this concept owns. No other concept may read or write it.
> Use paper-style relational notation: `field: SubjectType -> FieldType  -- multiplicity`
> Multiplicity annotations: `mandatory` | `optional` | `conditional mandatory: <condition>` | `zero or more`
> For stateless concepts write: `*None.* <ConceptName> is stateless.`

```
<fieldName>: <SubjectType> -> <FieldType>   -- mandatory
<fieldName>: <SubjectType> -> <FieldType>   -- optional
```

## Actions

<!-- ⚠️ OUTCOME ALIGNMENT CONTRACT
     Every output name in every action signature below MUST exactly match
     the outcome names used in the approved chain table(s) for this concept
     in `02b_chain-table/output/`. Outcome names are the contract between
     stages — a name that differs from the chain table by even one character
     will produce an invalid sync at Stage 03.

     Before naming any output:
       1. Open every `02b_chain-table/output/*.chain-table.md` that involves
          this concept.
       2. Copy the exact outcome strings from the Outcome column.
       3. Use those strings verbatim here — no synonyms, no renamings.

     If you need an outcome the chain table did not name, STOP. Return to
     Stage 02b and amend the chain table first. Do not invent outcomes here.

     Similarly: do not add state fields or action inputs that have no basis
     in the chain table or responsibility map. If a field is not in the chain
     table, raise it as an open question in the Notes section.
-->

> The verbs this concept exposes. Each action is a local function call
> from a sync or from `Web`.
>
> Two formats are available:
>
> **A. Precondition/postcondition (preferred for actions whose failures are pure state-guard violations):**
>   - Precondition failure → refusal (`:outcome "refused"`). No state change.
>     Syncs match on `[ refused ]`.
>   - Postcondition describes the state transition for happy path.
>   - Use this when the action either succeeds fully or is meaningless to
>     attempt (e.g. "look up a user that doesn't exist").
>
> **B. Case-split outcomes (for actions whose failures are state-mutating):**
>   - Each outcome is a named completion (`[ ok ]`, `[ error: "badPassword" ]`).
>   - Use this when a failure pathway still mutates state (e.g. incrementing
>     a failed-attempts counter).

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
