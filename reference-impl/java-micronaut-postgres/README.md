# reference-impl/java-micronaut-postgres/

A reference profile that maps the CLAD methodology onto Java + Micronaut with
**relational concept state** in Postgres, while keeping the shared in-memory
action log for coordination.

| Layer | Technology |
|---|---|
| Language | Java 21 |
| DI / HTTP runtime | Micronaut Platform 4.10.x |
| Coordination engine | `clad-engine` (shared, in-memory Jena action log) |
| Concept state | Postgres via JOOQ + Flyway (schema-per-application) |
| Tests | JUnit 5, Testcontainers (Postgres) |
| Architecture rules | ArchUnit 1.x |

The action log is **always in-memory RDF** — only concept state differs per
profile. Here, concept state is relational. See the sibling
[`java-micronaut-jena/`](../java-micronaut-jena/) profile for the RDF/SPARQL
realization of the same three concepts.

## Mapping methodology → this profile

| Methodology concept | Java realization |
|---|---|
| Concept | A package under `com.example.app.concepts.<name>` with one `*Concept` class extending `dev.clad.engine.ConceptAgent`, persisting state via JOOQ |
| Sync | A `final` class under `com.example.app.syncs` extending `dev.clad.engine.SyncAgent` (identical to the Jena profile) |
| Concept state | Flyway migrations under `src/main/resources/db/migration/`; JOOQ codegen into `com.example.app.db` |
| Action log | `dev.clad.engine.ActionLog` (in-memory), wired by `com.example.app.storage.JooqFactory` |
| Flow token | `dev.clad.engine.FlowManager` (unchanged) |

## The relational lowering

Stage 03b conceptual data models map to the schema deterministically via
Halpin's Rmap, specialized for CLAD — see [`RELATIONAL_LOWERING.md`](RELATIONAL_LOWERING.md).

Key rules:

- **One schema per application** (`public`); each table's name is prefixed by
  its owning concept (`user_accounts`, `passwordauth_credentials`,
  `session_tokens`).
- **No foreign key crosses a concept boundary.** Cross-concept identifiers are
  opaque typed columns. This is hard rule R2 at the DDL level.
- Mandatory → `NOT NULL`, optional → nullable, defaults → `DEFAULT`,
  uniqueness → `UNIQUE`.

## Build & test

```sh
# from the repo root
mvn test -f reference-impl/pom.xml -pl java-micronaut-postgres -am
```

The JOOQ codegen runs offline (`DDLDatabase` parses the Flyway SQL — no live DB
needed at build). The concept/flow tests spin up a real Postgres via
Testcontainers (`postgres:16-alpine`), so Docker must be available to run them.

## Running locally

```sh
docker run -d --name clad-pg -p 5432:5432 -e POSTGRES_DB=clad -e POSTGRES_USER=clad -e POSTGRES_PASSWORD=clad postgres:16-alpine
mvn -f reference-impl/pom.xml -pl java-micronaut-postgres -am mn:run
```

Then:

```sh
curl -X POST http://localhost:8080/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"ada","password":"correct-horse-battery-staple"}'
# => {"sessionToken":"<uuid>"}
```

Flyway runs at startup; the `DemoSeed` registers `ada`. The datasource is
configured in `src/main/resources/application.yml`.

## Debug introspection

The shared `DebugController` exposes `/api/dev/{flows,syncs,flow/{token},stuck,actions}`
(dev-only, opt-in). The RDF-only `/concept/{name}/triples` endpoint is not
present here — inspect concept state with `psql` (`SELECT * FROM user_accounts;`)
instead.
