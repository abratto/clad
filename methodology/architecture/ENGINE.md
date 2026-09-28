# The CLAD reference engine

> The fire-after-commit engine (`reference-impl/legible-engine/`,
> package `dev.legible.engine`) is the canonical runtime. It realises the
> Meng & Jackson synchronization semantics directly — no transactions, no
> RDF/SPARQL substrate. The older transactional-predicate engine
> (`dev.clad.engine`) was retired along with its Jena/RDF profile; the last
> version that contains it is tag `v0.4.0` (see
> `reference-impl/LEGACY.md` and `maintenance/fire-after-commit-engine.md`).

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
| `FactStore` / `Region` | `engine/FactStore.java`, `engine/Region.java` | Storage-agnostic relations; one `Region` per concept (R2). `InMemoryFactStore` is canonical; Postgres implements the SPI in `legible-storage`. |
| `ActionLog` | `engine/ActionLog.java` | Append-only record store of `Invocation`s and `Completion`s; per-flow, so flows never share mutable log state. |
| `Concept` | `engine/Concept.java` | A state machine whose actions are `Map execute(String action, Map input)` returning an `outcome` + fields. |
| `SyncRule` | `engine/SyncRule.java` | A declarative `when`/`where`/`then` rule (pure data, no branching — R3). |
| `WhereEvaluator` | `engine/WhereEvaluator.java` | The `where`-clause binding engine: trigger/sibling joins, constants, concept-state reads (Pattern D), fan-out, `OPTIONAL`, `bind(uuid)`, `?_eachthen` grouping, and route `Guard`s. |
| `SyncEngine` | `engine/SyncEngine.java` | Dispatches, commits, evaluates syncs, mints invocations; serializes concept actions per concept (the action is the atomic unit). |
| `FlowArchiver` / `FlowArchiveBuffer` | `engine/FlowArchiver.java` | Flush a completed flow to a sink + bounded buffer, then discard it. |
| `DebugApi` | `engine/DebugApi.java` | Introspection over the logs, archive buffer, fact store, and rules — direct record lookups (see "The debug surface"). |

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

## The action log — invocations and completions

Each flow owns one append-only `ActionLog`. An action is recorded as two
relational records, never one mutable object:

| Record | Fields | Committed |
|---|---|---|
| `Invocation` (request half) | `actionId`, `flowId`, `parentActionId`, `causedBySync`, `concept`, `action`, `input`, `invokedAt` | before the concept runs |
| `Completion` (result half) | `actionId`, `flowId`, `concept`, `action`, `outcome`, `fields`, `completedAt` | after the action returns |

`parentActionId` points at the action whose completion caused this invocation;
`causedBySync` names the `SyncRule` whose `then` emitted it. Those two provenance
edges are what make the realized chain reconstructible. Failures are ordinary
`Completion`s with a named `error` outcome — never an exception or a rollback.
See [`FLOW_TOKENS.md`](FLOW_TOKENS.md) for outcome casing and payload rules, and
[`SYNCHRONIZATIONS.md`](SYNCHRONIZATIONS.md) for the rule grammar.

## Sync dispatch — from a completion to the next invocation

Once a completion is committed (fire-after-commit), the engine finds the rules
that could fire **by index, not by scanning every rule**:

- At construction, `SyncEngine` builds a trigger index from
  `concept/action[/outcome]` to the rules (and conjuncts) that match it, in
  declaration order.
- For a committed completion the engine takes those candidate entries, then
  requires **every** conjunct of a (possibly multi-`when`) rule to have a
  matching committed completion in the same flow — the latest matching
  invocation per conjunct, filtered by the conjunct's input pattern (`ABSENT`
  honoured).
- A matched rule is emitted **at most once per trigger** (provenance-based
  exactly-once over the primary action + rule name); `where` is evaluated into
  frames and each frame appends one `then` invocation carrying
  `parentActionId`/`causedBySync`.
- New invocations are pushed onto the flow's pending queue and drained to
  quiescence. There is **no scheduler and no polling loop** — dispatch is a
  synchronous work queue over the flow's own log.

## The debug surface — designed vs realized chains

`SyncEngine.debug()` returns a `DebugApi` over the in-flight logs, the archive
buffer, the fact store, and the registered rules. The Micronaut profile exposes
it at `/api/dev/*` (disabled in `prod`). It answers two different questions:

| Endpoint | Answers |
|---|---|
| `/api/dev/syncs` | the **designed** chain — every registered `SyncRule`: name, trigger (`Concept/action (input: …)[Outcome]`), and `then` actions |
| `/api/dev/flow/{flowId}` | the **realized** chain — the ordered actions of one flow, each with `concept`/`action`/`input`, its committed `outcome`/`fields`, and the provenance edges `parentActionId`/`causedBySync`. Reconstruct the chain by following those edges. Falls back from the in-flight log to the archive buffer (`source: active-log \| archive-buffer \| none`). |
| `/api/dev/flows` | flow ids currently in flight |
| `/api/dev/stuck` | in-flight invocations with no completion (see below) |
| `/api/dev/concept/{name}/facts` | one concept region's facts |

`/syncs` is the spec; `/flow/{id}` is the trace. (The retired Jena profile
exposed this as SPARQL over an RDF action graph; the fire-after-commit engine
stores structured records, so these endpoints are direct lookups — see
[`SYNC_ENGINE_EVOLUTION.md`](SYNC_ENGINE_EVOLUTION.md).)

## Stuck, replay, and quiescence

Because each action commits its completion immediately after it runs, an
invocation with **no completion** means it was recorded but never processed.

- `stuck()` (`/api/dev/stuck`) lists exactly those in-flight invocations. It is
  a **liveness/integrity** signal, not a timeout: nothing polls for it.
- A *failing* action is not stuck — it completes with a named `error` outcome.
- In a healthy synchronous `run()` the flow drains to quiescence and is archived
  before the call returns, so `stuck` is empty; it is non-empty only while a flow
  is mid-drain, or after an interrupted drain (a crash between an invocation and
  its completion).
- `SyncEngine.drain(ActionLog)` is the explicit, idempotent replay entry point: it
  re-processes every uncompleted invocation, skipping any that already has a
  completion (`completion(id).isPresent()`).

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
