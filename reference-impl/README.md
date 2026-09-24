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
- [`java-legible/`](java-legible/) — the canonical in-memory profile and the
  engine's test/demo: the worked example's login feature plus `social`,
  `tagging`, and `token`, exercising the full sync model — fan-out, Pattern D
  reads, `OPTIONAL`, `?_eachthen` aggregation, `bind(uuid)`, route scoping, and
  the flow-token back-trace.
- [`java-micronaut/`](java-micronaut/) — the Micronaut HTTP
  Ports & Adapters profile: Micronaut for the HTTP transport, Postgres
  concept state via `RmapPostgresFactStore` (R-map-derived from the Stage
  03b data models; Flyway owns base DDL, jOOQ introspects it). Ships a
  `Dockerfile` + `docker-compose.yml` (local smoke) and a `fly.toml`
  (Fly.io deploy). Re-lowered from the legacy transactional engine — see
  `maintenance/reference-profiles-fire-after-commit.md`.
- [`legible-storage/`](legible-storage/) — the `PostgresFactStore`
  (generic fact relation) and `RmapPostgresFactStore` (typed table per
  concept). These show the engine is storage-agnostic: the same
  `Concept`/`SyncRule` code runs on in-memory or Postgres with identical
  outcomes. **CLAD ships in-memory and Postgres as supported backends**; any
  other backend — including an RDF/SPARQL triplestore — is a `FactStore`
  implementation you provide against the SPI.

## Retired: legacy transactional engine

The original transactional-predicate/RDF (Jena) stack — the `clad-engine`
module and the `java-micronaut-jena` profile — was **retired** after the
`java-micronaut` re-lowering. It is not built, checked, or
maintained here. The last version that contains it is tag `v0.4.0`; see
[`LEGACY.md`](LEGACY.md).

## Profiles at a glance

| Profile | Use it when you need | Transport | Concept state |
|---|---|---|---|
| `java-legible` | the engine's test/demo catalogue (seed features), in-memory | none / method call | in-memory `FactStore` |
| `java-micronaut` | **a real backend service** (HTTP; storage selectable) | Micronaut HTTP | in-memory (default) or Postgres (`clad.storage`) |

The worked example's zero-framework `java-plain` profile now lives with the
example:
[`../examples/java-plain/`](../examples/java-plain/) (standalone build).

**Transport and storage are independent.** The three profiles above pair a
transport choice with a storage choice; the engine sees only `FactStore`. To
build a Micronaut service on in-memory state, or a method-call app on Postgres,
keep the concepts, syncs, and `Web` bootstrap and change the `FactStore`
binding (`legible-storage/`; see
[`../methodology/implementation/STORAGE_MAPPING.md`](../methodology/implementation/STORAGE_MAPPING.md)).

## Why the engine was re-architected

The full evolution — sync-as-transaction SPARQL engine → fire-after-commit →
paper-faithful when-matching, with the standing capability comparison to the
paper authors' reference implementation — is
[`../methodology/architecture/SYNC_ENGINE_EVOLUTION.md`](../methodology/architecture/SYNC_ENGINE_EVOLUTION.md).

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
- **Storage is a profile detail.** `FactStore`/`Region` is the boundary. CLAD
  ships an in-memory backend (canonical) and a Postgres backend (durable); any
  other backend, including an RDF/triplestore one, is a `FactStore`
  implementation you provide.

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
