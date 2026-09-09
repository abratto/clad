# reference-impl/

This folder is a Maven reactor holding the CLAD **reference profiles** —
concrete language/framework choices that realise the WYSIWID pattern under
the hard rules in
[`../methodology/implementation/RULES.md`](../methodology/implementation/RULES.md).

## The fire-after-commit engine (canonical)

Since the engine re-architecture (`maintenance/fire-after-commit-engine.md`),
the canonical runtime is the **fire-after-commit engine**:

- [`legible-engine/`](legible-engine/) — a zero-dependency concept/sync
  engine (`dev.legible.engine`). Concepts hold state as relations behind a
  `FactStore` SPI; actions are map→map functions; syncs are declarative
  `when`/`where`/`then` rules. Coordination happens **after** an action is
  committed to a per-flow action log — there are no transactions and no
  rollback.
- [`java-plain/`](java-plain/) — the plain-Java quick-start: the login
  feature only, zero framework. No DI, no HTTP server — the transport
  surface is a method call. Start here.
- [`java-legible/`](java-legible/) — the canonical in-memory profile:
  UC-00-login plus example features (social, tagging, token) exercising the
  full sync model — fan-out, Pattern D reads, `OPTIONAL`, `?_eachthen`
  aggregation, `bind(uuid)`, route scoping, and the flow-token back-trace.
- [`java-micronaut-postgres/`](java-micronaut-postgres/) — the durable
  Ports & Adapters profile: Micronaut for the HTTP transport, Postgres
  concept state via `RmapPostgresFactStore` (R-map-derived from the Stage
  03b data models; Flyway owns base DDL, jOOQ introspects it). Ships a
  `Dockerfile` + `docker-compose.yml` (local smoke) and a `fly.toml`
  (Fly.io deploy). Re-lowered from the legacy transactional engine — see
  `maintenance/reference-profiles-fire-after-commit.md`.
- [`legible-storage/`](legible-storage/) — the `JenaFactStore`,
  `PostgresFactStore`, and `RmapPostgresFactStore` backends, proving the
  engine is storage-agnostic: the same `Concept`/`SyncRule` code runs on
  in-memory, Jena, and Postgres with identical outcomes.

## Legacy transactional engine

The original transactional-predicate engine remains only for the RDF/SPARQL
profile, until it too is re-lowered onto the fire-after-commit engine (no
further maintenance work should target it):

- [`clad-engine/`](clad-engine/) — the legacy RDF/SPARQL coordination
  engine (`dev.clad.engine`): `ActionLog`, `ConceptAgent`, `SyncAgent`,
  `SyncDispatcher`, `FlowManager`, `Storage`.
- [`java-micronaut-jena/`](java-micronaut-jena/) — Java 21 + Micronaut for
  HTTP, Apache Jena for per-concept RDF graphs (legacy RDF/SPARQL profile).

## Profiles at a glance

| Profile | Use it when you need | Transport | Concept state |
|---|---|---|---|
| `java-plain` | the smallest complete example / method-call quick start | none (method call) | in-memory `FactStore` |
| `java-legible` | the full sync-model catalogue (seed features) | none / method call | in-memory `FactStore` |
| `java-micronaut-postgres` | durable deployable stack (HTTP, SQL, containers, Fly.io) | Micronaut HTTP | Postgres (`RmapPostgresFactStore`) |
| `java-micronaut-jena` | the legacy transactional showcase (no new work) | Micronaut HTTP | Jena RDF named graphs |

## Why the engine was re-architected

The legacy engine encoded the older "sync-as-transaction" reading of
Jackson's *The Essence of Software*: `ConceptAgent.writeCompletion` performed
an *atomic composite write* (completion + downstream syncs in one Jena
transaction, with `abortBatch` rollback). Daniel Jackson's own forum reply
records that his student Eagon Meng's sync DSL "gets rid of the need for
transactions, and also allows much finer granularity" (see
[arXiv:2508.14511](https://arxiv.org/abs/2508.14511) and
[arXiv:2606.11051](https://arxiv.org/abs/2606.11051)).

The fire-after-commit engine follows that model directly:

- **The action is the atomic unit.** A concept action mutates only its own
  `Region`; a downstream failure is a named `outcome`, not an exception to
  roll back.
- **Syncs fire after commit.** No transaction spans concept boundaries; the
  action log (invocation + completion, with provenance edges) is the source
  of truth.
- **Storage is a profile detail.** `FactStore`/`Region` is the boundary;
  in-memory, Jena, and Postgres are interchangeable backends.

## Benefits

- **No transaction machinery.** No 2PC, saga, or compensating-action
  infrastructure; failures are first-class outcomes routed by syncs.
- **~100× lower latency, ~50× throughput** (measured against the Jena
  profile's own concurrency test — see
  [`java-legible`](java-legible/README.md)).
- **Concurrency without global locks.** Per-flow log sharding plus
  per-concept action serialisation (a concept is a state machine).
- **Richer provenance.** Every action carries `parentActionId` and
  `causedBySync`, so Stage 05 back-trace is a direct record lookup, not a
  graph reconstruction.

Other profiles (TypeScript/Deno, Kotlin/Ktor, Python/FastAPI, …) can be
added as sibling modules without changing anything in `methodology/`. The
methodology is profile-independent.
