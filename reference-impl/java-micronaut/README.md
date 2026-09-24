# reference-impl/java-micronaut/

The **Micronaut HTTP transport** reference profile on the fire-after-commit
engine: Micronaut for the HTTP adapter, with a **selectable concept-state
backend** — in-memory (default) or Postgres. The engine's `FactStore`/`Region`
SPI is the boundary, so the concepts and syncs are identical whichever backend
is active; only where state persists changes.

| Layer | Technology |
|---|---|
| Language | Java 21 |
| DI / HTTP runtime | Micronaut Platform 4.10.x |
| Coordination engine | `legible-engine` (fire-after-commit; in-memory action log) |
| Concept state | **selectable** via `clad.storage`: `memory` (default) or `postgres` |
| Postgres binding | `legible-storage`'s `RmapPostgresFactStore` (R-map, per-concept typed tables); Flyway owns base DDL, jOOQ codegen introspects it |
| Tests | JUnit 5, ArchUnit 1.x; Testcontainers (Postgres) only under the postgres binding |
| Deploy | `Dockerfile` + `docker-compose.yml`; `fly.toml` for Fly.io (Postgres binding) |

## Choosing the storage backend

`clad.storage` (in `application.yml`, overridable by env `CLAD_STORAGE`) selects
the `FactStore` binding:

| `clad.storage` | Binding | When |
|---|---|---|
| `memory` (default) | `InMemoryFactStore` | dev, tests, quick start — no database, no Docker |
| `postgres` | `RmapPostgresFactStore` (R-map typed tables) | durable deployment (Docker/Fly.io) |

The beans are gated by `@Requires(property = "clad.storage", …)`: the in-memory
factory is active unless postgres is selected, and the Postgres factory,
datasource, and `StoreInitializer` (Flyway + `createSchema`) are active only
then. Adding a third backend — e.g. an RDF triplestore — is a new `FactStore`
implementation plus a gated factory; the concepts, syncs, and transport do not
change.

## Package mapping (this profile's realization)

| Methodology concept | Java realization |
|---|---|
| Concept | one `*Concept implements dev.legible.engine.Concept` under `com.example.app.concepts.<name>`, state in the concept's own `Region` (R2) |
| Sync | one final `*Rule` carrier per `*.sync.md` under `com.example.app.syncs`, emitting a declarative `SyncRule` (R3); assembled by `LoginSyncRules.all()` |
| Web bootstrap (R4) | `WebController` and `LoginGateway` — normalize input, `engine.run("Web", "request", …)`, translate the authored `Web/respond` fields |
| Concept state | the injected `FactStore`: `InMemoryFactStore` or `RmapPostgresFactStore` (Stage 03b typed tables via `dev.legible.storage.LoginSchemas`) |
| Storage binding | `com.example.app.storage` — `MemoryStorageFactory` / `storage.postgres.PostgresStorageFactory`, selected by `clad.storage` |
| Flow token | the engine's action log + `causedBySync` lineage (unchanged across FactStore backends) |

The action log is **in-memory** in every fire-after-commit profile — only
concept state differs. The same `Concept`/`SyncRule` code the
[`java-legible`](../java-legible/) profile runs against `InMemoryFactStore`,
[`examples/java-plain/`](../../examples/java-plain/) boots method-only, and this profile runs against
whichever `FactStore` `clad.storage` selects, proven by `legible-storage`'s
`StorageContractTest`.

## Run it

```bash
# In-memory (default) — no database, no Docker:
mvn -f ../../pom.xml -pl java-micronaut -am test
mvn -f ../../pom.xml -pl java-micronaut -am exec:java -Dexec.mainClass=com.example.app.Application
# then: curl -X POST localhost:8080/login -d '{"username":"ada","password":"correct-horse-battery-staple"}' -H 'Content-Type: application/json'

# Postgres — Testcontainers-backed tests:
mvn -f ../../pom.xml -pl java-micronaut -am test -Dclad.storage=postgres
```

The demo seed registers `ada` / `correct-horse-battery-staple` on whichever
backend is active (`com.example.app.storage.DemoSeed`).

## Container + deploy

The container/deploy assets deploy the **Postgres** binding.

```bash
cd reference-impl/java-micronaut
docker compose up --build    # app + Postgres; smoke: POST /login per scenario
fly launch --no-deploy       # fly.io: creates app + Postgres, wires DATABASE_URL
fly deploy
```

`docker compose` is the test/local verification surface (manual smoke, not part
of the gate); `fly.toml` ships the Fly.io config — attach `fly postgres` in
launch and `DATABASE_URL`/`PGUSER`/`PGPASSWORD` are wired through
`application.yml`. Both set `CLAD_STORAGE=postgres`.

## Debug surface

`/api/dev/flows`, `/api/dev/flow/{flowId}`, `/api/dev/stuck`,
`/api/dev/concept/{name}/facts`, and `/api/dev/syncs` expose the engine's
runtime evidence (DebugApi): committed-but-unfinished actions, per-concept
region contents, and the registered sync rules. Disabled in `prod`.

## Not included (deliberate surface reduction)

The legacy version of this module also carried `AuthController` and
`GraphQLController` demo transports over the legacy transactional engine.
They were removed in the re-lowering (see
`maintenance/reference-profiles-fire-after-commit.md`); the login HTTP
surface plus the debug surface is the reference contract.
