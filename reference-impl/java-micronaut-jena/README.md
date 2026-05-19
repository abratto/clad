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

> Package note: `com.example.app` and `src/main/java` in this folder are
> reference-profile examples, not required CLAD defaults. In downstream
> projects, set package/source-root values in
> `features/UC-XX-<slug>/_config/package-and-layout.md` and generate code
> to those paths.

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

## SPARQL guidance (this profile only)

Use the rules below only when implementing CLAD with this Java/Jena
profile. They are not global CLAD rules.

1. Keep coordination in sync SPARQL fragments (`whereClause()` and
   `thenBindings()`); do not move domain branching into Java sync code.
2. Keep concept state in the owning concept graph (`concept:<name>`).
   Cross-concept state reads are forbidden (R2).
3. Join cross-concept facts via the action log and shared `?_flow` in the
   active action graph (`https://clad.dev/actions`).
4. In `whereClause()`, treat `?_when_1` and `?_flow` as engine-owned
   bindings. Use them; do not redefine them.
5. In `thenBindings()`, emit exactly one downstream invocation rooted at
   `?_then_1` with `:concept`, `:name`, and `:input ?_then_input`.
6. Keep outcomes explicit and literal (for example `"FOUND"`,
   `"WRONG_PASSWORD"`) so test intent maps remain stable.

Minimal sync fragment shape:

```java
@Override
protected String whereClause() {
     return
          "    ?_when_1 :concept <...> ;\n" +
          "             :name    \"...\" ;\n" +
          "             :flow    ?_flow ;\n" +
          "             :output  ?_out .\n" +
          "    ?_out :outcome \"...\" .\n";
}

@Override
protected String thenBindings() {
     return
          "    ?_then_1 :concept <...> ;\n" +
          "             :name    \"...\" ;\n" +
          "             :input   ?_then_input .\n" +
          "    ?_then_input :field ?value .\n";
}
```

For profile conventions and architecture guardrails, see
[`CODE_STYLE.md`](CODE_STYLE.md).

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

## Debugging flows locally

The reference impl now exposes **dev-only** WYSIWID introspection routes
under `/api/dev`, but only when both of these conditions are true:

- the Micronaut environment is not `prod`
- `clad.debug.endpoints.enabled=true` is set explicitly

These endpoints are for local debugging and flow inspection only; they
are not part of the business HTTP API.

For this Java profile, they are also the default runtime evidence
surface for CLAD Stage 04 implementation-time debugging and Stage 05
verification-time flow-token traceability.

Why this exists:

- humans can inspect the exact action-log and concept-state shape without
   dropping into ad hoc SPARQL queries
- weaker/local LLMs can be given a stable, read-oriented debugging
   surface instead of asking them to infer engine state from raw triples
- `/api/dev/flows` and `/api/dev/syncs` make the Stage 03/04 runtime
   wiring legible in the same vocabulary used by CLAD artefacts

How to enable it locally:

```sh
cd reference-impl/java-micronaut-jena
mvn -DskipTests package
java -Dclad.debug.endpoints.enabled=true \
       -jar target/clad-java-micronaut-jena-0.1.0-SNAPSHOT.jar
```

Use it when you need to answer questions like:

- which syncs are currently registered, and in what intended flow order?
- what happened for one specific flow token after the flow archived?
- which active actions are stuck without `:output`?
- what triples currently exist in one concept graph?

Operational notes:

- the controller is disabled by default; if you do not opt in, `/api/dev/*`
   returns `404`
- `DELETE /api/dev/actions` clears only the active action graph for local
   reset/debug loops; it does not clear archived flows or concept graphs
- `GET /api/dev/flow/{token}` accepts only CLAD flow-token IRIs and
   `GET /api/dev/concept/{name}/triples` accepts only lowercase
   alphanumeric concept names

- `GET /api/dev/flows` — registered syncs grouped by human-readable flow metadata
- `GET /api/dev/syncs` — flat list of registered syncs and any `@SyncMetadata`
- `GET /api/dev/flow/{token}` — action history for one flow token, including archived flows
- `GET /api/dev/stuck` — active actions that have no `:output`
- `DELETE /api/dev/actions` — clear the active action graph for local resets
- `GET /api/dev/concept/{name}/triples` — inspect all triples in `concept:{name}`

Example:

```sh
curl http://localhost:8080/api/dev/flows
curl http://localhost:8080/api/dev/stuck
curl http://localhost:8080/api/dev/concept/user/triples
# after a /login call, inspect one archived flow token:
curl http://localhost:8080/api/dev/flow/https%3A%2F%2Fclad.dev%2Fflow%2F<uuid>
```

Because completed flows are archived, `/api/dev/flow/{token}` remains
useful after a request has already produced `Web/respond`.

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
