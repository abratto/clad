<!-- Template for Stage 04b (04b_spec). Purpose: see methodology/implementation/STAGES.md §"Stage 04b — Spec". -->

# `<ConceptName>` — SPEC

> A SPEC is the contract slice of a concept that the implementation
> compiles against. It is derived mechanically from
> `<ConceptName>.concept.md`: action signatures, outcome enums, and
> flow-token shape — nothing else. No prose principle, no edge-case
> discussion; that lives in the concept spec.

## Actions

### `<actionName>(<arg1>: <Type1>, <arg2>: <Type2>, ...) -> <OutcomeRef>`

- **Inputs:** `<arg1>: <Type1>`, `<arg2>: <Type2>`
- **Outcomes (enum):** `<OUTCOME1>`, `<OUTCOME2>`, `<OUTCOME3>`
- **Flow token:** `<ConceptName>.<actionName> { <field1>, <field2>, <outcome> }`

### `<actionName>(...) -> <OutcomeRef>`  *(repeat per action)*

- **Inputs:** ...
- **Outcomes (enum):** ...
- **Flow token:** ...

## Response shapes

<!-- Optional. Include this section only when
     features/_system/stages/00_actor-goal/output/port-spec.md exists.
     Derive these assertions from the external adapter contract, not from
     implementation preference. -->

### `<METHOD> <path>`

- **Success wrapper:** `<JSON path or envelope>`
- **Required fields:**
  - `<json.path>` — `<type>` — `<notes>`
- **Primary error envelope:** `<exact JSON path/value shape>`
