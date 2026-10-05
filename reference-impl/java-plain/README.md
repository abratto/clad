# java-plain — the plain-Java durable profile

The durable stack with **no transport framework at all**: plain `main()` over
Flyway + `RmapPostgresFactStore` + the login example's concepts and syncs. The
point of the profile is the seam it demonstrates — engine and storage are
framework-free libraries (`legible-engine`, `legible-storage` carry zero
Micronaut imports), so an adopter brings *any* HTTP framework (Jetty, Spring,
Ktor, …) or none, without touching engine, storage, concepts, or syncs.

## Boot order (the whole contract)

`PlainPostgresApp.boot()`:

1. `PGSimpleDataSource` from the environment — `DATABASE_URL`
   (default `jdbc:postgresql://localhost:5432/clad`), `PGUSER`/`PGPASSWORD`
   (defaults `clad`/`clad`, mirroring `java-micronaut/application.yml`).
2. **Flyway migrates** — the schema owner runs before any store use
   (`V1__login_rmap.sql`, drift-guarded against `LoginSchemas.all()` exactly
   like the micronaut profile's migration; both render the same derivation).
3. `new RmapPostgresFactStore(dataSource, LoginSchemas.all())` — the derived
   R-map table set.
4. `LoginApp.create(store)` — the login flows (`Web.request` → … →
   `RespondForLogin…`), no HTTP in sight.

```java
LoginApp app = PlainPostgresApp.boot();
app.seedUser("ada", "correct-horse-battery-staple");
Map<String, Object> respond = app.login("ada", "correct-horse-battery-staple");
```

## Running

```bash
# Scripted scenario (OK / bad password) against a local Postgres:
DATABASE_URL=jdbc:postgresql://localhost:5432/clad \
  mvn -f ../pom.xml org.codehaus.mojo:exec-maven-plugin:3.5.0:java \
      -pl java-plain -Dexec.mainClass=dev.legible.plain.PlainPostgresApp

# Docker-backed boot test (Flyway owns schema, flows round-trip):
mvn -f ../pom.xml -pl java-plain test -Dclad.storage=postgres

# Docker-free: the drift guard runs; the container test skips
mvn -f ../pom.xml -pl java-plain verify
```

## Where it differs from `java-micronaut`

| | `java-plain` | `java-micronaut` |
|---|---|---|
| Transport | none (your choice) | Micronaut 4 HTTP adapter |
| Concept state | `RmapPostgresFactStore` | same (`clad.storage=postgres`) |
| Schema | own `V1` migration, own drift guard | same pattern, its own copy |
| jOOQ codegen | not needed (the store uses dynamic DSL) | introspects the migration |
| Adapter e2e gate | CLI scenario in `main()` | `LoginFlowTest` over HTTP |

Narrative: [`../../methodology/architecture/RELATIONAL_RMAP.md`](../../methodology/architecture/RELATIONAL_RMAP.md).
