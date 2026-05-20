# Storage mapping — realizing conceptual data models in a profile

CLAD's Stage 04a takes the approved conceptual data model from Stage
03b and maps it into the selected storage profile. This file is the
procedural reference for that mapping step.

## When this file applies

Stage 04a only. If the selected profile has no persistent store, Stage
04a writes `_NOT_APPLICABLE.md` and this file does not apply.

## What Stage 04a does

For each approved `<Name>.data-model.md`:

1. Choose the concept's storage region identifier in the selected
   profile.
2. Choose the profile-level identity/value representation needed to
   realize the approved object types and value types.
3. Map each approved fact type to the profile's storage primitive.
4. Map approved constraints to the profile's enforcement mechanism.
5. Record any profile-specific enforcement notes or explicit
   non-enforcement notes.

Stage 04a must not introduce new facts, fields, constraints, or helper
structures that were not already approved in Stage 03b.

Use [`../../templates/storage.md`](../../templates/storage.md) as the
default output shape unless the selected profile needs a stricter local
format. See [`../../templates/storage-rdf-example.md`](../../templates/storage-rdf-example.md)
for one concrete RDF / named-graph example based on the Java/Jena
reference profile.

## Profile guidance

### RDF / named-graph profiles

For RDF-backed profiles, the default CLAD stance is **fact realization
in triples, integrity checks in shapes/tests, and optional ontology
metadata only where the profile actually needs it**.

- Concept region → one named graph URI per concept
- Entity type → a subject IRI minting rule within the owning concept
   graph
- Value type → a literal/datatype mapping rule
- Binary fact type → one RDF predicate whose subject/object shape is
   documented in the mapping
- Higher-arity fact type → an objectified node only if the approved
   Stage 03b model already requires that objectification; do not invent
   reification structures ad hoc in Stage 04a
- Unary fact type → the mapping must follow the approved conceptual
   model explicitly; do not choose between class membership and boolean
   predicates by mapper taste alone
- Uniqueness, mandatory, value, and set/subtype constraints → SHACL,
   implementation checks, tests, or another explicit enforcement surface
   named in the mapping
- `rdfs:domain`, `rdfs:range`, and OWL axioms → optional ontology
   metadata, not the default persistence contract

RDF mappings must stay traceable to approved elementary facts. If RDF's
binary triple form would force extra helper nodes or predicates not
justified by the Stage 03b artifact, stop and repair the conceptual
model first.

### Relational profiles

- Fact type → column or relation
- Concept region → table or schema prefix owned by one concept
- Constraints → `UNIQUE`, `NOT NULL`, `CHECK`, lookup tables, etc.

### Document profiles

- Fact type → document field
- Concept region → one collection per concept
- Constraints → validator or schema layer

## Output shape

Write the result to `output/<Name>.storage.md` when mapping applies.
The file records the profile, the region identifier, and how each
approved fact type is realized. It should also say how object identity,
value typing, and constraint enforcement are handled in that profile.
If no persistent store exists, write `output/_NOT_APPLICABLE.md`
explaining why.