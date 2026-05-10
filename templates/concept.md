<!-- Template for Stage 02 (02_concepts). Purpose: see methodology/architecture/CONCEPTS.md. -->

# <ConceptName> — <one-line capability>

> Concept template. Fill in each section. Keep the whole file under one
> screen if you can.

## State

> The data this concept owns. No other concept may read or write it.

- `<field>: <Type>` — <what it represents>

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

### `<actionName>(<args>) -> <Outcome1> | <Outcome2>`

- **Inputs:** `<arg>: <Type>` — <meaning>
- **Outputs:** `<Outcome1>` — <when>; `<Outcome2>` — <when>
- **Effect on state:** <prose>
- **Flow token:** `{ action: "<ConceptName>.<actionName>", <fields> }`

## Operational principle

> One paragraph: a typical sequence of actions and what the user
> observes. This is the WYSIWID heart of the spec.

## Notes

> Optional. Edge cases, invariants, or open questions for the human
> reviewer.
