# Stage 03b — Data model

## Why this stage exists

This stage separates **conceptual data modeling** from implementation.
It turns each concept's approved `state` section plus any approved
Pattern D exposure from 03a into a **profile-neutral** fact model
before Stage 04 starts talking about RDF, SQL, document fields, or
other storage primitives.

**Feeds:**

- `<Name>.data-model.md` → 04a (profile-specific storage mapping), 04d (state invariants remain visible when implementation starts).

**Agent stance for this stage:** this stage models facts and
constraints, not databases. If you find yourself naming a table,
property IRI, migration, or schema library, you are too far downstream.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../02_concepts/output/` | 4 | Approved concept state sections |
| `../03a_dependency-review/output/pattern-d-summary.md` | 4 | Approved cross-concept fields that must be exposed conceptually |
| `../../../../methodology/architecture/DATA_MODEL_NOTES.md` | 3 | Conceptual data-model procedure |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R2 |
| `../../../../templates/data-model.md` | 3 | Output template |

## Process

For each approved concept spec, derive a profile-neutral conceptual data
model by following the seven CSDP steps in `DATA_MODEL_NOTES.md`.
The output must make those steps inspectable in text form: familiar
examples, elementary facts, draft fact model, combination/derivation
checks, uniqueness and arity, mandatory/logical derivations, value/set/
subtype constraints, and final checks. If a concept truly has no state,
still produce a `<Name>.data-model.md` file recording that fact rather
than skipping the concept silently.

Every fact and constraint must trace 1:1 to approved Stage 02 state or
approved Pattern D exposure from 03a. Do not add foreign keys,
cross-concept joins, storage-specific indexes, or implementation-only
helper fields.

## Outputs

- `output/<Name>.data-model.md` per concept — profile-neutral conceptual data model following the seven-step CSDP structure

## Verify

- One data-model file exists for every concept spec in `../02_concepts/output/`.
- Each `.data-model.md` makes all seven CSDP steps inspectable, even if
  some steps conclude `None` or `Not applicable`.
- Every fact type traces back to approved Stage 02 state or approved
  Pattern D exposure from 03a.
- Elementary facts are explicit and remain concept-local.
- No profile-specific storage primitives appear in the body of any
  `.data-model.md` file.
- No cross-concept foreign key or direct region-sharing relationship is
  introduced.
- Uniqueness constraints, mandatory role constraints, derivations, and
  value/set/subtype constraints are either stated explicitly or marked
  absent explicitly.
- **Cross-stage check (back):** every Pattern D field in
  `pattern-d-summary.md` appears in the owner concept's data model.

## Gate

Default human approval.

## Next stage

→ [`../04_implement/CONTEXT.md`](../04_implement/CONTEXT.md) — Implement (router)

To advance, the human says: **"Proceed to Stage 04."**