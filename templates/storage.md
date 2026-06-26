<!-- Template for Stage 04a (04a_storage-mapping). Purpose: see methodology/implementation/STORAGE_MAPPING.md. -->

> See `templates/storage-rdf-example.md` for one concrete RDF / named-graph example.

# <Concept> — storage mapping

## Profile

- Profile: `<profile name>`
- Region identifier: `<named graph / table / collection / other>`

## Identity and value realization

### Entity identity

- `<EntityType>` -> `<IRI minting rule / primary key rule / document identity rule>`

### Value typing

- `<ValueType>` -> `<literal datatype / column type / field type>`

## Fact realization

- `<Fact type from 03b>` -> `<storage primitive and shape>`
- `<Fact type from 03b>` -> `<storage primitive and shape>`

## Constraint enforcement

- `<Constraint from 03b>` -> `<SHACL / code / tests / DB constraint / validator / not enforced in storage>`
- `<Constraint from 03b>` -> `<enforcement surface>`

## Profile notes

- `<optional note about profile-specific realization choices>`

## Traceability check

- Every entry above traces to the approved `output/<Concept>.data-model.md`.
- No new fact, helper structure, or cross-concept storage read was introduced.