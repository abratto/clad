# Bootstrap concepts — transport boundary ownership

A **bootstrap concept** is the concept that owns a system's transport
boundary: it translates external signals into flow tokens (the entry
point) and translates concept outcomes back into transport responses
(the exit point). Every chain table starts and ends with a bootstrap
concept action.

`Web` is the HTTP bootstrap concept and is the primary example in
CLAD. Other transports use the same pattern under a different name:

| Transport | Bootstrap concept | Entry action | Exit action |
|---|---|---|---|
| HTTP / REST | `Web` | `handle(request)` | `respond(status, body)` |
| gRPC | `Grpc` | `receive(call)` | `reply(status, message)` |
| Kafka / event stream | `Stream` | `consume(event)` | `publish(topic, payload)` |
| CLI | `Cli` | `invoke(args)` | `print(exitCode, output)` |

Note on naming: the WYSIWID paper (Meng & Jackson, Onward! 2025)
calls the Web entry action `request`. CLAD uses `handle` instead,
because "handling" a request is more precise about what the bootstrap
concept does — it receives an HTTP request, normalises it, and routes
it into the action chain. The symmetry of `handle(request)` /
`respond(status, body)` also mirrors the request/response cycle more
naturally than `request(...)` / `respond(...)`. This is a controlled
divergence (see [`SYNCHRONIZATIONS.md`](SYNCHRONIZATIONS.md)).

The pattern is identical in all cases. Only the transport vocabulary
changes. Hard rule R4 applies to every bootstrap concept: **no
business concept may own a transport entry point**.

This file uses `Web` for all examples. Substitute the appropriate
bootstrap concept name and action vocabulary when working with a
different transport.

---

## What a bootstrap concept does

1. **Translate the transport signal into a single action.** The entry
   action (e.g. `Web.handle(request)`) receives the inbound signal and
   emits a flow token. That is its entire upstream job.
2. **Translate a result back into a transport response.** The exit
   action (e.g. `Web.respond(status, body)`) takes a result authored
   by a sync and writes the outbound response.
3. **Own the dispatch table.** The bootstrap concept knows which
   routes / methods / topics / commands exist. This table is data
   inside the concept; it is not metadata scattered across business
   concepts.

That is the whole responsibility list. A bootstrap concept has two
actions and one piece of state.

## What a bootstrap concept does **not** do

- **No business logic.** It does not validate domain invariants, query
  a database, hash a password, or decide whether a request is
  authorised. Those decisions live in concepts and are coordinated
  by syncs.
- **No reading another concept's state.** It honours R1 like every
  other concept.
- **No conditional branching on domain values.** The exit action can
  switch on transport-level status codes but not on domain outcomes
  like "wrong password vs. unknown user". Domain branching belongs to
  syncs whose `then` clause picks which exit action variant to fire.
- **No retries, no caching, no rate-limiting policy.** Those are
  cross-cutting concerns that, if needed, become their own concepts
  (`RateLimit`, `Cache`, ...) coordinated by syncs.
- **No transport docs as domain truth.** Generated OpenAPI / Swagger is
  a transport-facing description of the already-authored boundary, not a
  substitute for the use case, concept, sync, chain, or SPEC artefacts.

Transport-facing documentation such as OpenAPI is still useful and may
be generated directly from the bootstrap boundary. Keep it narrow:

- annotate the bootstrap controller / route and boundary DTOs
- document the inbound request and outbound `respond(status, body)` shape
- do not move domain rules, scenario branching, or concept semantics into
  the transport documentation layer

## Where response serialization belongs

The authored result is a domain-level outcome (status code + field-value
pairs). The sync spec declares it — for example,
`Web.respond(status=200, body={sessionToken: sessionId})`. The translation
of that authored result into a transport response (JSON/XML serialization,
header setting) belongs in the **transport boundary**, not in the engine
and not in sync code.

Specifically:

- **Syncs** author the response *shape* (status + field names). They do
  not assemble JSON, set HTTP headers, or perform I/O.
- **The engine** reads the completed `Web/respond` action from the action
  log and returns the field-value map to the caller. It does not serialize
  the map to JSON or any other format.
- **The transport boundary** (controller / route handler) receives the
  field-value map and converts it to a typed DTO or passes it to the
  profile's JSON serializer. This is where format-specific concerns like
  JSON escaping, content-type negotiation, and response-header setting
  belong.

A reference profile that uses string concatenation to build JSON inside
the engine (`buildJsonBody()`) has violated this boundary. The fix is to
move response serialization to the transport boundary and let a standard
JSON library (Jackson, Gson, etc.) handle it.

## Optional `Web/format` action

The paper's case study (Appendix C.1) introduces an additional bootstrap
concept action called `Web/format` that factors out response assembly
when a single HTTP response needs data from multiple concepts. CLAD
supports this as an **optional** pattern for complex response shapes.

The basic pattern:

```
sync FormatArticleResponse
when {
    Web/format: [ type: "article" ; article: ?article ; request: ?request ] => []
}
where {
    Article: { ?article title: ?title ; body: ?body ; slug: ?slug ; author: ?author }
    User: { ?author name: ?authorName }
    Profile: { ?author profile: ?profile . ?profile bio: ?authorBio ; image: ?authorImage }
    OPTIONAL { Tag: { ?article tag: ?tag } }
    BIND ( ?article AS ?_eachthen )
}
then {
    Web/respond: [ request: ?request ; body: [ article: [ slug: ?slug ; ... ] ] ]
}
```

Use `Web/format` when a response body aggregates fields from two or more
concepts (e.g. an article plus its author's profile). In simple cases
where the response is a single concept's output (e.g. `Session.grant`
returning a `sessionId`), a direct sync from the concept action to
`Web/respond` is cleaner and does not need `Web/format`.

When `Web/format` is used, it counts as a concept action in the
responsibility map and appears in chain tables as an intermediate step
between the last business concept action and the final `Web/respond`.

## Implementation check for Stage 04

When implementing a bootstrap concept, the allowed shape is narrow:

1. normalize the inbound transport payload into the root action input
2. call the flow root (`Web.handle(...)` or profile equivalent)
3. await the authored result
4. translate the authored result into the outbound transport response

Everything else is suspect and should be treated as a boundary
violation unless the methodology explicitly says otherwise.

Concrete anti-patterns:

- calling business concept classes directly from the controller / route
  handler
- branching on domain outcomes inside the controller / route handler
- computing business dates, identifiers, status transitions, or policy
  inside the transport boundary
- reading or mutating business concept state from the transport boundary
- matching the final HTTP output while bypassing the action/sync chain

If a flow can only be made green by putting domain logic in the
bootstrap concept, the problem is upstream: the concept/spec/sync set
is incomplete and should be repaired there.

The Java reference profile adds a heuristic source-level check here as
well: `Web` infrastructure classes must not contain imperative
branching (`if` / `switch`) unless a transport-only exception is marked
explicitly in source. The waiver marker is
`CLAD-ALLOW-TRANSPORT-BRANCH`.

## How a bootstrap concept participates in the chain

Every chain table (Stage 02b) starts with the bootstrap concept's
entry action and ends with its exit action. The middle rows are
business concepts. This makes the transport boundary *visible* in the
choreography rather than ambient.

```mermaid
sequenceDiagram
    participant Client
    participant Web
    participant <BusinessConcept>
    Client->>Web: HTTP request
    Web->>Web: handle(request) — emits flow token
    Web-->>Web: (sync fires on Web.handle)
    Web->>+<BusinessConcept>: action(...)
    <BusinessConcept>-->>-Web: outcome
    Web-->>Web: (sync fires on outcome)
    Web->>Client: respond(status, body)
```

## Why bootstrap concepts are not in `02_concepts/output/`

Stage 02 writes one `<Name>.concept.md` per *business* concept.
Bootstrap concepts are fixtures of the system, not domain concepts;
their anatomy is documented here rather than in a per-feature concept
file. Stage 02a's responsibility map lists the bootstrap concept (so
its row is visible in coverage checks) and points its *Notes* column
at this document.

## Responsibility map rule

Every responsibility map must include a row for the bootstrap concept
that owns this feature's transport boundary. A map without a bootstrap
concept row is incomplete: the chain has no entry point and no exit
point. The 02a CONTEXT.md Verify section enforces this as a named
check.

## Reviewing for R4 violations

Look for these symptoms:

- A `@Controller`/`@Get`/`@Post` annotation (or transport equivalent)
  outside the bootstrap concept's package.
- A business concept that takes a transport request object as an
  argument.
- A sync whose `then` clause speaks transport verbs directly instead
  of calling the bootstrap concept's exit action with a domain result.
- A new concept named `*Controller`, `*Endpoint`, `*Consumer`, or
  `*Handler` — those names are a smell that the bootstrap concept's
  job is being split.

Any of these means R4 has slipped. The fix is always: move the
transport surface back into the bootstrap concept and replace the
violation with a sync.

## Profile reference

The Java/Micronaut/Jena profile implements `Web` as a single
`WebController` class. Other profiles (Node/Express, Python/FastAPI,
Go/net-http, ...) implement the same two actions over their respective
frameworks. A gRPC profile would implement `Grpc` as a single
`GrpcServer` class with the same two-action contract.
