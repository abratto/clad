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
| Concept | A package under `com.example.app.concepts.<name>` containing exactly one `*Concept` class that `extends ConceptAgent` |
| Sync | A `final` class under `com.example.app.syncs` that `extends SyncAgent` and declares `whereClause()` + `thenBindings()` |
| `Web` (HTTP entry) | `com.example.app.infrastructure.WebController` — `@Controller("/login")` calling `FlowManager.rootAction` then `SyncDispatcher.awaitResponse` |
| Flow token | A UUID IRI minted by `FlowManager.mintFlowToken()`; carried by every action node in the chain via the `:flow` predicate |
| Action log | `com.example.app.engine.ActionLog` — wraps a Jena transactional `Dataset`. Concept state lives in named graphs `concept:<name>`; the active log lives in `https://clad.dev/actions`; archived flows in `https://clad.dev/actions/archive` |
| Scheduler | `com.example.app.engine.SyncDispatcher` — the only loop in the system |
| Hard rules R1–R5 | Enforced by `LegibleArchitectureRulesTest` (ArchUnit) |

See [`../../methodology/architecture/ENGINE.md`](../../methodology/architecture/ENGINE.md)
for engine internals (trigger index, dedup edge, flow archival).

## Build

```sh
cd reference-impl/java-micronaut-jena
mvn test
```

`mvn test` runs the ArchUnit suite **and** the outside-loop
`LoginFlowTest`, which boots an embedded Micronaut server and exercises
all three UC-00 scenarios (success, wrong password, unknown user)
end-to-end through the dispatch loop.

## Running locally

```sh
mvn -DskipTests package
java -jar target/clad-java-micronaut-jena-0.1.0-SNAPSHOT.jar
# in another terminal:
curl -X POST http://localhost:8080/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"ada","password":"correct-horse-battery-staple"}'
# => {"sessionToken":"<uuid>"}
```

`Application.DemoSeed` registers user `ada` with the known password
above at startup; remove it in any non-demo profile.

## Status

The engine is **fully wired** and the UC-00-login flow runs end-to-end:
the three concepts (`User`, `PasswordAuth`, `Session`) and the six
syncs (`LoginRequestStartsLookup`, `LoginLookupTriggersAuth`,
`LoginGrantsSession`, `LoginRespondSuccess`, `LoginRespondWrongPassword`,
`LoginRespondUnknownUser`) produce the predicted token chains in
[`features/UC-00-login/stages/04_implement/04c_flow-tests/output/login-flow-test.md`](../../features/UC-00-login/stages/04_implement/04c_flow-tests/output/login-flow-test.md).

The Jena dataset is in-memory transactional
(`DatasetFactory.createTxnMem()`); a TDB2 / Fuseki backend is the next
profile-level extension.

See [`CODE_STYLE.md`](CODE_STYLE.md) for the conventions every
contributor (human or agent) should follow inside this profile.
