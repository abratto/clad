# The CLAD legacy reference engine

> Status: this document describes the legacy sequential polling engine in
> `reference-impl/java-micronaut-jena/`. The profile defaults to its
> transactional predicate engine, which matches the WYSIWID synchronization
> semantics and is recommended for new projects. Other profiles are free to
> reuse, replace, or reimplement either engine, provided they honour the
> WYSIWID hard rules in [`../implementation/RULES.md`](../implementation/RULES.md).

## What the engine does

The engine is the runtime that turns the static spec — concepts and syncs —
into an executable system. Given a single HTTP request:

1. **Mint a flow token** for the request and write a root
   `Web/request` action node into the RDF action log.
2. **Drive concept agents** that poll the log for unprocessed input nodes
   addressed to them, run their action body, and write `:output` triples.
3. **Drive sync agents** that fire declarative `INSERT … WHERE …` rules
   whenever new completion triples match their `when` clause; this writes
   the next downstream action node into the log.
4. **Loop steps 2–3** until a `Web/respond` completion appears for the
   originating flow token, then translate it into an `HttpResponse` and
   archive the flow.

There is **no Java event bus**. Every coordination decision is read from
and written to RDF triples in the Jena dataset. The semaphore-based
[`CompletionBus`](../../reference-impl/clad-engine/src/main/java/dev/clad/engine/CompletionBus.java)
is a pure scheduling hint: it carries only "concept X completed
something", never any per-action data. This invariant is what
WYSIWID Rule 4 demands ("the running system *is* what is described";
the description is the RDF graph, not in-memory routing).

## Components

| Component | File | Responsibility |
|---|---|---|
| `RdfVocabulary` | `engine/RdfVocabulary.java` | Schema IRIs, named-graph names, and predicate constants. |
| `ActionLog` | `engine/ActionLog.java` | Owns the Jena `Dataset`; runs SPARQL `UPDATE`/`CONSTRUCT`/`ASK`/`SELECT` in transactions; archives completed flows. |
| `CompletionBus` | `engine/CompletionBus.java` | Semaphore + concurrent set of triggered concept IRIs. |
| `FlowManager` | `engine/FlowManager.java` | Mints flow tokens; writes the root `Web/request` action node. |
| `ConceptAgent` | `engine/ConceptAgent.java` | Polls for pending invocations of a given action name; writes `writeCompletion` / `writeRefusal` / `writeError` triples. |
| `SyncAgent` | `engine/SyncAgent.java` | Declares `syncName`, `whereClause`, `thenBindings`, and `trigger`. The base class assembles a single `INSERT … WHERE …` SPARQL update with a per-sync dedup edge so each `when` invocation fires once. |
| `SyncDispatcher` | `engine/SyncDispatcher.java` | The only scheduler. Indexes syncs by trigger concept and by target concept; on each tick, runs the concept agents whose work is pending, then batches every triggered sync's SPARQL into a single update. |

## The trigger index

`SyncDispatcher` precomputes two maps at startup:

- `triggerIndex : conceptIri → List<SyncAgent>` — which syncs care that a
  given concept just completed an action.
- `pendingInvocationIndex : conceptIri → List<ConceptAgent>` — which
  concept agents own the IRI that any sync's `then` clause schedules
  work into.

On each dispatch tick the dispatcher drains the `CompletionBus`, looks up
syncs in `triggerIndex`, runs them as a batched SPARQL `UPDATE`, then
schedules the affected concept agents for the next tick. This avoids the
naive *poll-everything* loop while keeping the scheduler stateless about
what each sync actually does.

## Flow archival

When a `Web/respond` completion is observed for a flow token,
`ActionLog.archiveFlow(flowToken)` moves every triple owned by the flow —
the action nodes, their inputs, and their outputs — from the active
graph (`https://clad.dev/actions`) into the archive graph
(`https://clad.dev/actions/archive`) in a single atomic transaction.
This keeps the live graph small and gives `05_verify` a stable place to
trace from.

## Maintenance contract

Engine and profile maintenance must preserve these properties unless the
change re-enters the affected feature artefact chain:

- every completed action retains exactly one causal flow token;
- a sync's deduplication edge prevents duplicate downstream invocations;
- a flow is wholly active, wholly archived, or wholly deleted, never split
   between those states;
- scheduling may change implementation strategy but not observable action
   outcomes, causal order, or response contracts;
- declared storage configuration selects that backend or fails clearly; it
   must not silently fall back to a different backend.

The governed procedure for changing this layer is the maintenance route in
[`../core/ITERATIVE_CHANGES.md`](../core/ITERATIVE_CHANGES.md). Its test matrix
must exercise the applicable invariant at unit, integration, flow-regression,
or smoke level.

## Why this shape

Two design constraints from Meng & Jackson's *Legible Software*
(see [`../reference/CITATIONS.md`](../reference/CITATIONS.md)) drove the
engine:

1. **Concepts are independent.** A concept's only legal way to learn
   about another concept's effect is to read the action log. This is
   why the engine refuses to put per-action data on the
   `CompletionBus` — a Java-level routing object would re-introduce
   cross-concept coupling out of the architect's view.
2. **Syncs are declarative.** A sync's only legal way to coordinate
   across concepts is a SPARQL pattern over the log. This is why
   `SyncAgent` has no callbacks, no event handlers, and no domain
   branching — just `whereClause()` and `thenBindings()`.

## History

This engine is adapted from the WYSIWID engine of
Tastetag — a private companion project where the same author iterated on the runtime
shape against a richer set of concepts (Account, Alias, Product, Tag,
Preference, …). The CLAD copy keeps the algorithmic core intact and
strips the application surface down to a single `Web` controller plus
the three concepts UC-00-login needs. See [`../../NOTICE`](../../NOTICE)
for provenance.
