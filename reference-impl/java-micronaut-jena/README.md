# reference-impl/java-micronaut-jena/

A reference profile that maps the CLAD methodology onto a concrete
Java stack:

| Layer | Technology |
|---|---|
| Language | Java 21 |
| DI / HTTP runtime | Micronaut 4.x |
| Persistence vocabulary | Apache Jena 5.x (RDF / SPARQL) |
| Tests | JUnit 5 |
| Architecture rules | ArchUnit 1.x |

This profile is **optional**. Methodology rules live in
[`../../methodology/`](../../methodology/) and are profile-agnostic;
this folder is one way to implement them.

## Mapping methodology → this profile

| Methodology concept | Java realisation |
|---|---|
| Concept | A package under `com.example.app.concepts.<name>` containing exactly one `*Concept` class |
| Sync | A class under `com.example.app.syncs` whose body is declarative `when … then …` |
| `Web` (HTTP entry) | `com.example.app.infrastructure.WebConcept` (only HTTP entry; R4) |
| Flow token | `com.example.app.engine.FlowToken` |
| Flow-token log | `com.example.app.engine.ActionLog` (in-memory; an RDF-backed implementation is the next step) |
| Hard rules R1–R5 | Enforced by `LegibleArchitectureRulesTest` (ArchUnit) |

## Build

```sh
cd reference-impl/java-micronaut-jena
mvn -DskipTests compile
mvn test
```

`mvn test` runs the ArchUnit suite. Domain tests added under
`features/UC-XX/stages/04*/output/` start `@Disabled`; the outside-in
TDD discipline turns them on as the inner loops go green.

## Status

This is **scaffolding only**:

- The engine (`ActionLog`, `FlowManager`) is in-memory.
- No real Jena store is wired yet (only the dependency); the next
  iteration adds an `RdfActionLog`/`RdfConceptStore` honouring R2
  ("one named graph per concept").
- `WebConcept` exposes no real endpoints; it only exists to anchor
  R4 ArchUnit checks.
- The three login concepts (`User`, `PasswordAuth`, `Session`) are
  minimal stubs — just enough for `LegibleArchitectureRulesTest` to
  not be vacuous and for the UC-00-login flow-test stubs to compile.

See [`CODE_STYLE.md`](CODE_STYLE.md) for the conventions every
contributor (human or agent) should follow inside this profile.
