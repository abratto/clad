# The CLAD reference engine

> The fire-after-commit engine (`reference-impl/legible-engine/`,
> package `dev.legible.engine`) is the canonical runtime. It realises the
> Meng & Jackson synchronization semantics directly — no transactions, no
> RDF/SPARQL substrate. The older transactional-predicate engine
> (`reference-impl/clad-engine/`, `dev.clad.engine`) remains as the Jena/
> Postgres profiles are re-lowered; see the maintenance record
> `maintenance/fire-after-commit-engine.md`.

## What the engine does

The engine turns the static spec — concepts and syncs — into an
executable system. Given one transport request:

1. **Mint a flow token** and append a root `Web/request` invocation to a
   fresh per-flow action log.
2. **Dispatch the invocation** to its concept, which runs its action
   (a map→map function over its own `Region`) and returns an `outcome`
   plus named fields.
3. **Commit the completion** to the log — *fire-after-commit*: the
   completion is durable in the log before any sync is evaluated.
4. **Evaluate syncs** whose `when` clause matches the completion;
   evaluate each `where` clause into frames and append one downstream
   invocation per frame (`then`), with provenance edges (`parentActionId`,
   `causedBySync`).
5. **Loop 2–4** to quiescence, then read the `Web/respond` completion and
   return its fields to the transport boundary.

There is **no Java event bus, no polling loop, no transaction and no
rollback.** A downstream action that fails simply completes with a named
`error` outcome — an ordinary committed fact. A crash mid-chain leaves a
pending invocation that a later drain re-processes idempotently (the
`completion(id).isPresent()` guard).

## Components

| Component | File | Responsibility |
|---|---|---|
| `FactStore` / `Region` | `engine/FactStore.java`, `engine/Region.java` | Storage-agnostic relations; one `Region` per concept (R2). `InMemoryFactStore` is canonical; Jena/Postgres implement the SPI. |
| `ActionLog` | `engine/ActionLog.java` | Append-only record store of `Invocation`s and `Completion`s; per-flow, so flows never share mutable log state. |
| `Concept` | `engine/Concept.java` | A state machine whose actions are `Map execute(String action, Map input)` returning an `outcome` + fields. |
| `SyncRule` | `engine/SyncRule.java` | A declarative `when`/`where`/`then` rule (pure data, no branching — R3). |
| `WhereEvaluator` | `engine/WhereEvaluator.java` | The `where`-clause binding engine: trigger/sibling joins, constants, concept-state reads (Pattern D), fan-out, `OPTIONAL`, `bind(uuid)`, `?_eachthen` grouping, and route `Guard`s. |
| `SyncEngine` | `engine/SyncEngine.java` | Dispatches, commits, evaluates syncs, mints invocations; serializes concept actions per concept (the action is the atomic unit). |
| `FlowArchiver` / `FlowArchiveBuffer` | `engine/FlowArchiver.java` | Flush a completed flow to a sink + bounded buffer, then discard it. |
| `DebugApi` | `engine/DebugApi.java` | Introspection (the old `/api/dev/*` SPARQL surface, now direct record lookups). |

## Concurrency model

- **Per-flow logs (sharding).** Each `run()` owns a private `ActionLog`,
  so flows never contend on log state.
- **Per-concept serialization.** A concept is a state machine; its actions
  run one at a time (`SyncEngine.execute` holds a per-concept lock). This
  makes "the action is the atomic unit" hold under concurrency without any
  storage-level coordination.
- **Storage-owned atomicity** remains available for profiles that need
  finer granularity (per-subject locks, or `SELECT … FOR UPDATE` in SQL).

## Flow archival

When a flow reaches quiescence, `FlowArchiver.archive` flushes its
`FlowRecord` (ordered invocations + completions, with provenance) to a
`FlowArchiveSink` and a bounded `FlowArchiveBuffer`, then discards the
transient per-flow log. The action log is transient execution state — not
durable business state — so memory stays bounded.

## Maintenance contract

Engine and profile maintenance must preserve these properties unless the
change re-enters the affected feature artefact chain:

- every action's completion is committed before any sync fires on it;
- a sync fires at most once per trigger (provenance-based exactly-once);
- the observable action chain and outcomes match the chain table (the
  flow-token back-trace in `05_verify`);
- declared storage backend (`FactStore` implementation) is selected or
  fails clearly — never a silent fallback.

The governed procedure for changing this layer is the maintenance route in
[`../core/ITERATIVE_CHANGES.md`](../core/ITERATIVE_CHANGES.md).

## Why this shape

Two design constraints from Meng & Jackson's *Legible Software* and
*Making Software Meaningful* (see
[`../reference/CITATIONS.md`](../reference/CITATIONS.md)) drove the engine:

1. **Concepts are independent.** A concept's only legal way to learn
   about another concept's state is a sync's `where` clause reading that
   concept's `Region` — never an in-process call.
2. **Syncs are declarative, and fire after commit.** A sync is a
   `when`/`where`/`then` rule with no callbacks, no branching, no
   transactions; it reacts to an already-committed completion.
