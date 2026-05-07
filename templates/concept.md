<!-- Template for Stage 02 (02_concepts). Purpose: see methodology/architecture/CONCEPTS.md. -->

# <ConceptName> — <one-line capability>

> Concept template. Fill in each section. Keep the whole file under one
> screen if you can.

## State

> The data this concept owns. No other concept may read or write it.

- `<field>: <Type>` — <what it represents>

## Actions

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
