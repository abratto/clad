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

### Using the predicate engine (default)

When you create a new CLAD project with the Java profile, concepts should
extend `PredicateConceptAgent` instead of `ConceptAgent`. This gives you
pre-commit sync evaluation, unmatched-outcome rejection, and atomic
batch writes.

```java
// In your concept class — e.g. UserConcept.java
import com.example.app.engine.predicate.PredicateConceptAgent;
import com.example.app.engine.predicate.PredicateSyncDispatcher;

public class UserConcept extends PredicateConceptAgent {

    @Inject
    public UserConcept(ActionLog log, CompletionBus bus,
                       PredicateSyncDispatcher dispatcher) {
        super(log, bus, dispatcher);
    }
    // ... rest of concept: conceptIRI, pollAll, processInvocation
}
```

Syncs and the FlowManager are unchanged — they work identically under
both engines. The only migration step is the base class and constructor.
If you already have concepts extending `ConceptAgent`, change them to
`PredicateConceptAgent` and add `PredicateSyncDispatcher` to their
constructor. The `processInvocation()` method is unchanged.

To use the reference engine instead (e.g. for learning or debugging
the step-by-step dispatch loop), set `engine.mode=reference` in
`clad.properties` and have concepts extend `ConceptAgent`.

For a side-by-side walkthrough of the same 3-concept chain in both
engines, see [`WORKED_EXAMPLE_ENGINES.md`](WORKED_EXAMPLE_ENGINES.md).

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
CucumberTest, which boots an embedded Micronaut server and exercises
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

### Docker Compose — full stack (app + Fuseki + Ollama)

Deploy the entire CLAD stack as a single unit — no local Java, Maven,
or model downloads needed on the host:

```sh
export FUSEKI_ADMIN_PASSWORD="replace-with-a-strong-secret"
mvn package -DskipTests
docker compose up --build
```

`FUSEKI_ADMIN_PASSWORD` is required; Compose deliberately has no insecure
default. The profile sends the password to Fuseki through
`CLAD_FUSEKI_PASSWORD` and bounds connection establishment to five seconds.
On an authentication challenge, the client sends credentials once and stops
after a second rejection; it never retries a completed SPARQL update.

The Compose endpoint uses HTTP only on its private Docker network. Deployments
that place Fuseki outside that network must use an HTTPS endpoint and a
least-privilege service account instead of an administrator credential.

This brings up three services that talk to each other by Docker service name:

| Service | Port | Purpose |
|---|---|---|
| `app` | 8080 | Micronaut + concepts + syncs + engine |
| `fuseki` | 3030 | Apache Jena Fuseki TDB2 triplestore (persistent concept state) |
| `ollama` | 11434 | Local LLM runtime (CPU or GPU) |

One-time model pull (after first startup):

```sh
docker compose exec ollama ollama pull llama3.2:3b
```

Configure the app via environment variables in `docker-compose.yml`:
`CLAD_LLM_MODEL` (model name), `CLAD_LLM_ENDPOINT` (Ollama URL),
`ENGINE_DATASET_TYPE=fuseki`, and `CLAD_FUSEKI_ENDPOINT` (Fuseki SPARQL
endpoint). The Compose profile also supplies `CLAD_FUSEKI_USERNAME` and
`CLAD_FUSEKI_PASSWORD`; set `FUSEKI_ADMIN_PASSWORD` before startup to override
the development default. Persistent volumes for Fuseki data and Ollama models
survive container restarts.

To stop: `docker compose down`. To rebuild after code changes:
`docker compose up -d --build`.

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

### Backend configuration

The engine's Dataset backend is configured via `clad.properties`, container
environment variables, or JVM system properties. The precedence is JVM system
property, environment variable, `clad.properties`, then the documented default.
All backends share the same engine code — concepts, syncs, and the dispatch
loop are unchanged.

| Key | Default | Description |
|---|---|---|
| `engine.dataset.type` | `tmemory` | `tmemory` / `tdb2` / `tdb2mem` / `fuseki-embedded` / `fuseki` |
| `engine.dataset.tdb2.dir` | `./clad-tdb2-store` | TDB2 data directory (for `tdb2` and `fuseki-embedded`) |
| `engine.dataset.fuseki.endpoint` | (required) | SPARQL service URL for `fuseki` backend |
| `engine.dataset.fuseki.port` | `0` (random) | Port for `fuseki-embedded` admin server |
| `engine.archive.flows` | `true` | Archive completed flows for debugging; set `false` in production |
| `engine.dispatch.timeout.seconds` | `5` | Max dispatch loop wall-clock time before returning 500 |
| `clad.dispatch.timeout.seconds` | `5` | System-property override for dispatch timeout |

Container environment names are `ENGINE_DATASET_TYPE`,
`ENGINE_DATASET_TDB2_DIR`, `CLAD_FUSEKI_ENDPOINT`,
`CLAD_FUSEKI_USERNAME`, and `CLAD_FUSEKI_PASSWORD`. A `fuseki` backend without
an endpoint fails at startup rather than falling back to local memory.

#### Available backends

**`tmemory` (default)** — in-memory Jena TxnMem Dataset. Zero-setup,
fastest single-request latency. Write batching eliminates contention
errors under concurrency (0 errors at 32 threads). Best for development
and testing.

```
p50: 7ms (1 thread), 8ms (32 threads)  |  0 errors  |  ~130 req/s
```

**`tdb2`** — persistent Jena TDB2 store via local directory. MR+SW
concurrency model. On macOS, per-commit `fsync` (~225ms) limits
single-request latency. On Linux (`fsync` ~10× faster), projected
~150ms p50. Suitable for single-node Linux production.

```
p50: 1,173ms (macOS, 1 thread)  |  errors at 4+ threads  |  ~0.6 req/s
```

**`fuseki-embedded`** — TDB2 with an embedded Fuseki HTTP admin server
on a random port. Same storage characteristics as `tdb2`; adds
`/$/stats`, `/$/ping`, and admin endpoints. Jetty 12 is pinned to
`12.0.14` (Micronaut BOM manages to `12.1.x` which is incompatible).

```
p50: 1,294ms (macOS, 1 thread)  |  same as tdb2 + admin UI
```

**`fuseki`** — remote Fuseki/SPARQL endpoint over HTTP. All SPARQL
operations delegate to an `RDFLinkHTTP` connection. Fuseki's internal
transaction batching reduces commit overhead (3.6× faster than direct
TDB2 on macOS). Zero contention errors — Fuseki serializes writes
safely in its MR+SW queue. Tested with `stain/jena-fuseki` Docker image.

```
p50: 325ms (macOS, 1 thread), 788ms (4 threads)  |  0 errors  |  ~4 req/s
```

#### Switching backends

```properties
# Development (default)
engine.dataset.type=tmemory

# Local persistent TDB2
engine.dataset.type=tdb2
engine.dataset.tdb2.dir=./data/tdb2-store

# Standalone Fuseki (Docker — tested with stain/jena-fuseki)
#   docker run -d --name fuseki -p 3030:3030 -e ADMIN_PASSWORD=admin stain/jena-fuseki
engine.dataset.type=fuseki
engine.dataset.fuseki.endpoint=http://localhost:3030/ds

# Embedded Fuseki (TDB2 + admin UI)
engine.dataset.type=fuseki-embedded
engine.dataset.tdb2.dir=./data/tdb2-store
```

Backends are selected at startup; changing the property requires a restart.

### Engine mode — reference vs. predicate

CLAD ships two sync dispatch engines, configured via `clad.properties`:

```properties
engine.mode=reference   # sequential dispatch (default)
engine.mode=predicate   # transactional predicate evaluation
```

**Reference engine** (`engine/reference/`) — the original dispatch loop,
kept for educational clarity. Each concept action commits independently.
The SyncDispatcher polls for completed actions and fires matching syncs.
Used in the UC-00-login worked example and the Conduit project. 

**Predicate engine** (`engine/predicate/`) — evolved from the reference
engine to implement the formal synchronization semantics from Meng &
Jackson's WYSIWID paper. ~3× faster due to batch-write transaction
batching. This is the **default** and the recommended engine for all
new CLAD projects.

The reference engine remains in `engine/reference/` for educational
clarity — it walks the architecture step by step (poll → fire → signal).
Select it with `engine.mode=reference` if you want to trace the dispatch
loop for learning purposes. Key
differences:

| Behavior | Reference engine | Predicate engine |
|---|---|---|
| When syncs are evaluated | After concept commits (poll event) | Before concept commits (predicate check) |
| Unmatched outcomes | Silently succeed (no sync fires) | Rejected — `SyncEvaluationException` thrown |
| A→B composite writes | Independent commits (window of inconsistency) | Single Jena transaction via `beginBatch/flushBatch` |
| Web/respond | Always succeeds | Always succeeds (exempt) |
| Concept isolation | Enforced by ArchUnit (R1) | Enforced by ArchUnit (R1) — unchanged |

The predicate engine's `PredicateConceptAgent` extends `ConceptAgent` and
overrides `writeCompletion()`. Before writing anything, it asks the
`PredicateSyncDispatcher` which syncs match the proposed outcome. If no
sync matches (and the action isn't Web/respond), the completion is
rejected before any state mutation. If syncs match, the completion and
all sync invocations are batched into a single Jena transaction — a
reader never sees Concept A updated without Concept B invoked.

This aligns with the paper's model: *"An action a_A in Concept A and an
action a_B in Concept B occur co-instantaneously."* The predicate engine
evaluates the synchronization as a logical constraint over the combined
action space, then commits the composite transition atomically.

Concepts, syncs, SPARQL syntax, the stage pipeline, and quality-gate
scripts are identical across both engines. Switching modes requires only
the property change — no code or artefact changes needed.

### Architecture: a modular monolith

CLAD's WYSIWID architecture produces a **modular monolith** — not a
distributed system. Concepts are code-level boundaries, not network
boundaries. All concepts live in one JVM, all state lives in one Jena
`Dataset` (in-memory or TDB2-backed), and synchronizations execute as
SPARQL within the same transaction context.

This is intentional and matches the paper: *"Concepts are modular
software boundaries, not distributed system boundaries."* The guarantee
of atomic composite writes (A's outcome + B's invocation in one
transaction) requires a shared transaction coordinator. In CLAD, that
coordinator is the Jena Dataset.

```
┌─────────────────────────────────────────────────────────────┐
│                    SINGLE JVM PROCESS                       │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Concept: User │  │Concept:Session│  │Concept:Auth   │   │
│  │ (isolated pkg)│  │ (isolated pkg)│  │ (isolated pkg)│   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘   │
│          │                  │                  │           │
│          └──────► PredicateSyncDispatcher ◄────┘           │
│                            │                                │
└────────────────────────────│────────────────────────────────┘
                             ▼
               ┌─────────────────────────┐
               │   Jena Dataset (TxnMem  │
               │   or TDB2)              │
               │                         │
               │   BEGIN ... COMMIT      │
               │   cross-graph atomic    │
               └─────────────────────────┘
```

**What you get:** total code isolation (no cross-concept imports, enforced
by ArchUnit), zero-cost transactional guarantees (concepts share a
transaction engine), and predictable latency (no network hops between
concepts).

**What you trade off:** per-concept runtime isolation (all concepts share
a process) and per-concept storage isolation (all concepts share a
Dataset). If you need independent scaling per concept, you're looking at
a different architecture than WYSIWID — and you'll face the same
tradeoffs every distributed system faces:

- **2PC/XA**: true predicate guarantees across databases, but high
  latency, reduced availability.
- **Saga/eventual consistency**: decoupled writes, but the predicate is
  violated between steps — compensating actions required.

The modular monolith is not a compromise — it's the architecture the
paper describes. Future CLAD work on distributed concepts would be a
new engine mode, not a replacement for this one.

#### Performance summary (Apple M4 Pro, 64 GB RAM, macOS)

| Backend | p50 (1 thr) | p50 (4 thr) | Max req/s | Errors | Persistence |
|---|---|---|---|---|---|
| `tmemory` | 7ms | 18ms | ~130 | 0 | No |
| `fuseki` (standalone) | 325ms | 788ms | ~4 | 0 | Yes (TDB2 via Fuseki) |
| `tdb2` | 1,173ms | timeout | ~0.6 | yes | Yes |
| `fuseki-embedded` | 1,294ms | — | — | — | Yes (TDB2) |
| `tdb2mem` | 13ms | — | — | block corruption | No |

The `tmemory` → `fuseki` → `tdb2` (Linux) progression covers the full
development-to-production pipeline. All backends share the same Storage
interface (`engine/Storage.java`); adding a new backend is a single
class implementing that interface plus a factory branch.

## Status

The engine is **fully wired** and the UC-00-login flow runs end-to-end
across all five backends. The three concepts (`User`, `PasswordAuth`,
`Session`) and seven rule-shaped syncs produce the predicted token chains
exercised by the Gherkin flow tests. The injectable Dataset architecture
(`Storage` interface, `CladDatasetFactory`) supports swapping backends
with a single property change. Write batching eliminates TxnMem
contention errors; RemoteStorage delegates SPARQL over HTTP to
standalone Fuseki with zero errors under concurrency.

See [`CODE_STYLE.md`](CODE_STYLE.md) for the conventions every
contributor (human or agent) should follow inside this profile.
