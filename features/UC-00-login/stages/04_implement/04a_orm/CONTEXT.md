# Stage 04a — ORM (UC-00-login)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept state sections |
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
