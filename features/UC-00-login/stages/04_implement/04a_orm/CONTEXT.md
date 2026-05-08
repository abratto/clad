# Stage 04a — ORM (UC-00-login)

## Why this stage exists

For profiles with a persistent store, this is where each concept's
`state` section becomes a concrete schema in **its own named region**
(hard rule R2). Drafting the schema **before** writing tests catches
"this field needs to be there because flow X reads it via Pattern D"
defects in 30 seconds rather than later inside a failing test.

In this feature the chosen profile is in-memory — see
[`output/_NOT_APPLICABLE.md`](output/_NOT_APPLICABLE.md). The CONTEXT
is kept so that, if the feature later gains a persistence profile, the
contract is already in place.

**Feeds:**

- `<Name>.orm.md` (or `_NOT_APPLICABLE.md`) → 04d (the test fixture builds against this schema), and the runtime data layer in the profile.

**Agent stance for this stage:** if a Pattern D field from
`pattern-d-summary.md` is missing from the owning concept's region, do
not "add it to make the column exist" — go back to Stage 02 and add it
to `state` first.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept state sections |
| `../../03a_dependency-review/output/pattern-d-summary.md` | 4 | Cross-concept fields, if any (UC-00 has none) |
| `../../../../../methodology/architecture/ORM_NOTES.md` | 3 | Seven-step procedure (when applicable) |
| `../../../../../reference-impl/java-micronaut-jena/README.md` | 3 | Profile storage status |

## Process

The Java profile is currently **in-memory only**: each concept owns
its state field directly (R2 enforced today by R1's no-cross-import
rule). No relational/RDF schema is needed. Document the decision in
`output/_NOT_APPLICABLE.md` and move on.

## Outputs

- `output/_NOT_APPLICABLE.md`

## Verify

- The note explains why ORM is skipped and how R2 is satisfied without it.

## Gate

Default.
