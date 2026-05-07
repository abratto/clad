# The `Web` concept — sole bootstrap surface

`Web` is a **bootstrap concept**: it is the only concept allowed to
own an HTTP entry point (hard rule R4). Every business concept stays
on its side of the wire and is invoked only through syncs that fire
on `Web.handle` flow tokens.

This file describes what `Web` does, what it does not do, and how to
recognise a `Web` violation in code review.

---

## What `Web` does

1. **Translate HTTP into a single action.** `Web.handle(request)`
   takes the incoming HTTP request and emits a flow token. That is
   `Web`'s entire upstream job.
2. **Translate a result back into HTTP.** `Web.respond(token,
   status, body)` takes a result (typically authored by a sync) and
   writes the HTTP response.
3. **Own the route table.** `Web` knows which URL paths exist and
   which method is allowed on each. The route table is data inside
   `Web`; it is not metadata scattered across business concepts.

That is the whole responsibility list. `Web` has two actions:
`handle` and `respond`. It has one piece of state: the route table.

## What `Web` does **not** do

- **No business logic.** `Web` does not validate domain invariants,
  query a database, hash a password, or decide whether a request is
  authorised. Those decisions live in concepts and are coordinated
  by syncs.
- **No reading another concept's state.** `Web` honours R1 like
  every other concept. If a sync needs `User.lookupByUsername` to
  decide a response shape, the *sync* calls it, not `Web`.
- **No conditional branching on domain values.** `Web.respond` can
  switch on HTTP status (200/400/401/...) but not on domain
  outcomes like "wrong password vs. unknown user". Domain branching
  belongs to syncs whose `then` clause picks which `Web.respond`
  variant to fire.
- **No retries, no caching, no rate-limiting policy.** Those are
  cross-cutting concerns that, if needed, become their own concepts
  (`RateLimit`, `Cache`, ...) coordinated by syncs.

## How `Web` participates in the chain

Every chain table (Stage 02b) starts with `Web.handle` and ends with
`Web.respond`. The middle rows are business concepts. This is what
makes `Web` *visible* in the choreography rather than ambient — a
reviewer can see exactly where the HTTP boundary is in every
scenario.

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

## Why `Web` is not in `02_concepts/output/`

Stage 02 writes one `<Name>.concept.md` per *business* concept.
`Web` is a fixture of the system, not a domain concept; its
`<Name>.concept.md` would just restate this file. Stage 02a's
responsibility map lists `Web` (so its row is visible in coverage
checks) and points its *Notes* column at this document.

## Reviewing for R4 violations

Look for these symptoms:

- A `@Controller`/`@Get`/`@Post` annotation outside the `Web` (or
  equivalent) package.
- A business concept that takes an `HttpRequest` (or framework
  equivalent) as an argument.
- A sync whose `then` clause speaks HTTP verbs ("respond 401")
  instead of calling `Web.respond(...)` with a domain result.
- A new concept named `*Controller` or `*Endpoint` — that name is a
  smell that `Web`'s job is being split.

Any of these means R4 has slipped. The fix is always: move the HTTP
surface back into `Web` and replace the violation with a sync.

## Profile reference

The Java/Micronaut/Jena profile implements `Web` as a single
`WebController` class under
`reference-impl/java-micronaut-jena/src/main/java/com/example/app/infrastructure/`.
Other profiles (Node/Express, Python/FastAPI, ...) would implement
the same two actions over their respective frameworks.
