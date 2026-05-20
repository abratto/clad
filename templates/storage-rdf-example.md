<!-- Worked example for Stage 04a (04a_storage-mapping). Illustrative only: based on the UC-00 User concept and the Java/Jena reference profile. -->

# User — storage mapping

## Profile

- Profile: `reference-impl/java-micronaut-jena` (RDF named-graph profile)
- Region identifier: `concept:user`

## Identity and value realization

### Entity identity

- `User` -> subject IRI `https://clad.dev/concept/user#user/<userId>`

### Value typing

- `UserId` -> realized inside the subject IRI path segment `<userId>`
- `Username` -> string literal object of `https://clad.dev/concept/user#username`

## Fact realization

- `User is identified by UserId.` -> no separate triple; the user identifier is realized by the subject IRI minting rule.
- `User has Username.` -> triple in graph `concept:user` of the form `<https://clad.dev/concept/user#user/<userId>> <https://clad.dev/concept/user#username> "<username>"`

## Constraint enforcement

- `Each UserId identifies at most one User.` -> enforced by the subject-IRI minting rule and UUID generation in concept code
- `Each Username identifies at most one User.` -> enforced by concept code and tests (`lookupByUsername` / `register` path), not by SHACL in the current reference profile
- `Every User has exactly one Username.` -> enforced by concept code; storage layer assumes the triple is present for persisted users
- `Every User has exactly one UserId.` -> enforced by the IRI minting rule; no second identifier slot exists in storage

## Profile notes

- This profile stores concept state in one named graph per concept and keeps cross-concept coordination out of concept graphs.
- The mapping uses the concept-local namespace `https://clad.dev/concept/user#` for predicates and user-node IRIs.
- No `rdfs:domain`, `rdfs:range`, or OWL axioms are required for this persistence mapping.

## Traceability check

- Every entry above traces to the approved `output/User.data-model.md`.
- No new fact, helper structure, or cross-concept storage read was introduced.