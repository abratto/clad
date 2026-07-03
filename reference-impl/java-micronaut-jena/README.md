# reference-impl/java-micronaut-jena/

A reference profile that maps the CLAD methodology onto a concrete
Java stack:

| Layer | Technology |
|---|---|
| Language | Java 21 |
| DI / HTTP runtime | Micronaut Platform 4.10.16 |
| Persistence vocabulary | Apache Jena 5.x (RDF / SPARQL) |
| Tests | JUnit 5 |
| Architecture rules | ArchUnit 1.x |

This profile is **optional**. Methodology rules live in
[`../../methodology/`](../../methodology/) and are profile-agnostic;
this folder is one way to implement them.

Downstream-template rule: if you create a new repository from CLAD and
choose this Java profile, copy the starter engine/code shape into your
own application root or service folder and evolve it there. Keep this
directory as a clean reference profile; do not turn
`reference-impl/java-micronaut-jena/` itself into your product's main
codebase.

Example copy-out pattern:

```sh
mkdir -p app/backend
cp -R reference-impl/java-micronaut-jena/. app/backend/
# then set real downstream paths in:
#   features/UC-XX-<slug>/_config/package-and-layout.md
# for example:
#   APP_PACKAGE_ROOT=org.acme.billing
#   APP_SOURCE_ROOT=app/backend/src/main/java
#   APP_TEST_SOURCE_ROOT=app/backend/src/test/java
```

> Package note: `com.example.app` and `src/main/java` in this folder are
> reference-profile examples, not required CLAD defaults. In downstream
> projects, set package/source-root values in
> `features/UC-XX-<slug>/_config/package-and-layout.md` and generate code
> to those paths.

Subpackage note: after substituting your real `APP_PACKAGE_ROOT`, keep
the same artifact-to-package mapping used by this profile: `api` for
boundary DTOs, `infrastructure` for HTTP/bootstrap adapters, `engine`
for runtime/framework classes, `concepts.<name>` for concept agents,
and `syncs` for declarative syncs. Do not scatter those class kinds
into arbitrary sibling packages.

This profile also treats generated OpenAPI as a **transport artefact**.
Swagger/OpenAPI annotations belong on the HTTP boundary and boundary DTOs,
not on concepts or syncs. The generated spec documents the authored
`Web/respond` surface; it does not replace Stage 01-04 CLAD artefacts as
the source of domain truth.

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

For the deterministic lowering contract from approved Stage 03 syncs to
`SyncAgent` SPARQL fragments, see [`SYNC_LOWERING.md`](SYNC_LOWERING.md).
That document is the profile-specific source of truth for how Pattern
A/B/C/D bindings, sink syncs, and the bootstrap handoff map into
`whereClause()` / `thenBindings()`.

The canonical working example for that lowering is the UC-00 login sync
pack under `src/main/java/com/example/app/syncs/`, together with
`engine/SyncAgent.java`. Those classes now demonstrate the reference
profile style directly: Java text blocks for SPARQL fragments,
`.formatted()` for IRI constants, explicit outcome literals kept inline,
and non-outcome string literals bound through
`SyncAgent.parameterizeSparql(...)`.

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
7. Write sync fragments as Java text blocks and interpolate only IRI
   constants with `.formatted()`.
8. For route names, shared response messages, and other non-outcome
   string literals, declare a Java constant and bind it through
   `SyncAgent.parameterizeSparql(...)` rather than embedding the literal
   directly in the fragment text.

Minimal sync fragment shape:

```java
@Override
protected String whereClause() {
   return """
      ?_when_1 :concept <%s> ;
             :name    "..." ;
             :flow    ?_flow ;
             :output  ?_out .
      ?_out :outcome "..." .
      """.formatted(CONCEPT_IRI);
}

@Override
protected String thenBindings() {
   return """
      ?_then_1 :concept <%s> ;
             :name    "..." ;
             :input   ?_then_input .
      ?_then_input :field ?value .
      """.formatted(TARGET_CONCEPT_IRI);
}

@Override
protected String parameterizeSparql(String sparql) {
   return bindLiteral(sparql, "_route", ROUTE);
}
```

For profile conventions and architecture guardrails, see
[`CODE_STYLE.md`](CODE_STYLE.md).

When writing executable syncs, use this README for profile overview,
[`CODE_STYLE.md`](CODE_STYLE.md) for package/architecture constraints,
and [`SYNC_LOWERING.md`](SYNC_LOWERING.md) for the actual spec-to-SPARQL
translation recipe.

## Canonical exemplar

When Stage 04 implementation work needs a concrete Java/Jena/Micronaut
shape to copy, use [`CANONICAL_EXEMPLAR.md`](CANONICAL_EXEMPLAR.md).

For the concrete sync coding pattern, copy from the UC-00 login sync
classes, not from older string-concatenation snippets in downstream
repositories.

Important: this exemplar is a **realization pattern**, not a substitute
for a feature's own approved upstream artefacts. Implementation must be
derived first from Stage 02 / 03 / 04 artefacts and only then mapped
into this profile's code shape.

In downstream CLAD-derived repositories, older imperative code,
coordinator classes, or mixed architectural styles must not be treated
as canonical precedent just because they exist in the tree.

That rule applies especially to copied template repositories: keep one
clean reference profile and copy from it into your real app root rather
than accumulating product code inside the profile seed itself.

## Build

```sh
cd reference-impl/java-micronaut-jena
mvn test
```

`mvn test` runs the ArchUnit suite **and** the outside-loop
`LoginFlowTest`, which boots an embedded Micronaut server and exercises
all three UC-00 scenarios (success, wrong password, unknown user)
end-to-end through the dispatch loop.

The same build also generates an OpenAPI spec at
`META-INF/swagger/clad-java-reference-api-0.1.0.yml` and a Swagger UI view
under `META-INF/swagger/views/swagger-ui`.

## Running locally

```sh
mvn mn:run
# in another terminal:
curl -X POST http://localhost:8080/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"ada","password":"correct-horse-battery-staple"}'
# => {"sessionToken":"<uuid>"}
```

If you are staying at the repository root instead of `cd`-ing into this
module, run the same goal against this profile's POM explicitly:

```sh
mvn -f reference-impl/java-micronaut-jena/pom.xml mn:run
```

If you want a packaged handoff artifact instead of the dev run loop:

```sh
mvn -DskipTests package
java -jar target/clad-java-micronaut-jena-0.1.0-SNAPSHOT.jar
```

With the app running, the generated transport docs are available at:

- `/swagger/clad-java-reference-api-0.1.0.yml`
- `/swagger-ui` (redirects to `/swagger-ui/index.html`)

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
- every authored HTTP response also carries `X-Flow-Token`, so a manual
   `curl` or browser call can be traced back to `/api/dev/flow/{token}`
   without a special test harness

How to enable it locally:

```sh
cd reference-impl/java-micronaut-jena
mvn mn:run -Dclad.debug.endpoints.enabled=true
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
curl -i -X POST http://localhost:8080/login \
   -H 'Content-Type: application/json' \
   -d '{"username":"ada","password":"correct-horse-battery-staple"}'
# response headers include:
# X-Flow-Token: https://clad.dev/flow/<uuid>

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
the three concepts (`User`, `PasswordAuth`, `Session`) and the seven
rule-shaped syncs (`WhenWebHandleRoutedThenUserLookupByUsernameForLogin`,
`WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin`,
`WhenUserLookupByUsernameNotFoundThenWebRespondForLogin`,
`WhenPasswordAuthCheckOkThenSessionGrantForLogin`,
`WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin`,
`WhenPasswordAuthCheckLockedThenWebRespondForLogin`, and
`WhenSessionGrantGrantedThenWebRespondForLogin`) produce the predicted token chains exercised
by the Gherkin flow tests in
`features/UC-00-login/stages/04_implement/04c_flow-tests/output/login.feature`.

The Jena dataset is in-memory transactional
(`DatasetFactory.createTxnMem()`); a TDB2 / Fuseki backend is the next
profile-level extension.

See [`CODE_STYLE.md`](CODE_STYLE.md) for the conventions every
contributor (human or agent) should follow inside this profile.
