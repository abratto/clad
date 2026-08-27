# reference-impl/

This folder is a Maven reactor holding one or more **implementation
profiles**: concrete language/framework choices that realise the WYSIWID
pattern under the hard rules in
[`../methodology/implementation/RULES.md`](../methodology/implementation/RULES.md).

The reactor is:

- [`pom.xml`](pom.xml) — parent POM (shared versions + Micronaut BOM).
- [`clad-engine/`](clad-engine/) — the shared, profile-agnostic
  action-log coordination engine (`dev.clad.engine`): `ActionLog`,
  `ConceptAgent`, `SyncAgent`, `SyncDispatcher`, `FlowManager`, `Storage`,
  and friends. The action log is always in-memory Jena; only concept-state
  persistence differs per profile.
- [`java-micronaut-jena/`](java-micronaut-jena/) — Java 21 + Micronaut
  for HTTP/runtime, Apache Jena for per-concept RDF graphs (the reference
  profile for RDF/SPARQL concept state).
- [`java-micronaut-postgres/`](java-micronaut-postgres/) — Java 21 +
  Micronaut for HTTP/runtime, JOOQ + Flyway + Postgres for concept state
  (the reference profile for relational concept state). The action log is
  still the shared in-memory `clad-engine`.

Other profiles (TypeScript/Deno, Kotlin/Ktor, Python/FastAPI, …) can be
added as sibling modules without changing anything in `methodology/`. The
methodology is profile-independent.

For repositories created from the CLAD template, treat this directory as
an **upstream reference shelf**, not as the main product code root. If
you choose one of these profiles, copy the selected profile's starter
code into your own runtime/app directory and add a dependency on
`clad-engine` (or copy it too) — do not fork the engine into each
profile. Do not mix downstream business code back into `reference-impl/`,
or the starter profile stops being a clean exemplar.
