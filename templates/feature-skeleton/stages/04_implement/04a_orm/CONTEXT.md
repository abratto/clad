# Stage 04a — ORM (optional state model)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs (state sections) |
| `../../03a_dependency-review/output/pattern-d-summary.md` | 4 | Every cross-concept field that must be exposed in this concept's region |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R2 |
| `../../../../../methodology/architecture/ORM_NOTES.md` | 3 | Seven-step drafting procedure (CLAD adaptation of Jarrar CSDP) |
| Profile reference docs (e.g. `reference-impl/<profile>/README.md`) | 3 | Storage conventions |

## Process

If the chosen profile uses a relational/RDF/document store, draft the
state schema for each concept by walking the seven-step procedure in
`ORM_NOTES.md` — one named region per concept (R2). Otherwise write
`_NOT_APPLICABLE.md` explaining why and skip.

## Outputs

- `output/<Name>.orm.md` per concept (one row per state field, with type and constraints), **or**
- `output/_NOT_APPLICABLE.md` if the profile does not use a persistent store

## Verify

- Each concept's schema lives in exactly one named region.
- No region is shared across concepts.
- Every field listed in `03a_dependency-review/output/pattern-d-summary.md`
  is present in the owner concept's region.

## Gate

Default human approval.
