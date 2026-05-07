# Stage 04a — ORM (optional state model)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs (state sections) |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R2 |
| Profile reference docs (e.g. `reference-impl/<profile>/README.md`) | 3 | Storage conventions |

## Process

If the chosen profile uses a relational/RDF/document store, draft the
state schema for each concept — one named region per concept (R2).
Otherwise write `_NOT_APPLICABLE.md` explaining why and skip.

## Outputs

- `output/<Name>.orm.md` per concept (one row per state field, with type and constraints), **or**
- `output/_NOT_APPLICABLE.md` if the profile does not use a persistent store

## Verify

- Each concept's schema lives in exactly one named region.
- No region is shared across concepts.

## Gate

Default human approval.
