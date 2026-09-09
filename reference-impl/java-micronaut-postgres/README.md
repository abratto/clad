# reference-impl/java-micronaut-postgres/

The **Ports & Adapters + Postgres** reference profile on the
fire-after-commit engine: Micronaut for the HTTP transport adapter,
Postgres for durable concept state (schemas *derived* from the Stage 03b
data models), companion guidance for running the same stack in Docker
Compose and on Fly.io.

| Layer | Technology |
|---|---|
| Language | Java 21 |
| DI / HTTP runtime | Micronaut Platform 4.10.x |
| Coordination engine | `legible-engine` (fire-after-commit; in-memory action log) |
| Concept state | Postgres via `legible-storage`'s `RmapPostgresFactStore` (R-map, per-concept typed tables) |
| Base DDL | Flyway (`V1__login_rmap.sql` mirrors the R-map derivation); jOOQ codegen introspects it |
| Tests | JUnit 5, Testcontainers (Postgres), ArchUnit 1.x |
| Deploy | `Dockerfile` + `docker-compose.yml`; `fly.toml` for Fly.io |

## Package mapping (this profile's realization)

| Methodology concept | Java realization |
|---|---|
| Concept | one `*Concept implements dev.legible.engine.Concept` under `com.example.app.concepts.<name>`, state in the concept's own `Region` (R2) |
| Sync | one final `*Rule` carrier per `*.sync.md` under `com.example.app.syncs`, emitting a declarative `SyncRule` (R3); assembled by `LoginSyncRules.all()` |
| Web bootstrap (R4) | `WebController` and `LoginGateway` — normalize input, `engine.run("Web", "request", …)`, translate the authored `Web/respond` fields |
| Concept state | R-map-derived typed tables (Stage 03b) via `dev.legible.storage.LoginSchemas`; Flyway owns base DDL (`V1__login_rmap.sql`) |
| Flow token | the engine's action log + `causedBySync` lineage (unchanged across FactStore backends) |

The action log is **in-memory** in every fire-after-commit profile — only
concept state differs. The same `Concept`/`SyncRule` code the
[`java-legible`](../java-legible/) profile runs against
`InMemoryFactStore`, [`java-plain`](../java-plain/) boots method-only, and
this profile runs against `RmapPostgresFactStore`, proven by
`legible-storage`'s `StorageContractTest`.

## Run it

```bash
mvn -pl java-micronaut-postgres -am test     # Testcontainers-backed tests
mvn -f ../../pom.xml -pl java-micronaut-postgres -am exec:java -Dexec.mainClass=com.example.app.Application
# then: curl -X POST localhost:8080/login -d '{"username":"ada","password":"correct-horse-battery-staple"}' -H 'Content-Type: application/json'
```

The demo seed registers `ada` / `correct-horse-battery-staple`
(`Application.DemoSeed`).

## Container + deploy

```bash
docker compose up --build    # app + Postgres; smoke: POST /login per scenario
fly launch --no-deploy       # fly.io: creates app + Postgres, wires DATABASE_URL
fly deploy
```

`docker compose` is the test/local verification surface (manual smoke, not
part of the gate); `fly.toml` ships the Fly.io config — attach `fly
postgres` in launch and `DATABASE_URL`/`PGUSER`/`PGPASSWORD` are wired
through `application.yml`.

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
