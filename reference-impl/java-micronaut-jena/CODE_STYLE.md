# Code style — `reference-impl/java-micronaut-jena/`

Profile-specific conventions. These do **not** apply to the
methodology folder; they exist because Java + Micronaut + Jena
imposes its own grain.

## Packages

```
com.example.app
├── engine                  RDF vocab, ActionLog, FlowManager, ConceptAgent, SyncAgent, SyncDispatcher, CompletionBus
├── infrastructure          WebController (sole HTTP entry; R4)
├── api                     DTOs for HTTP boundary
├── concepts.<name>         Exactly one *Concept class per package; extends ConceptAgent
└── syncs                   Declarative when/then rules (one final class per sync, extends SyncAgent)
```

Treat this package split as the **canonical Java profile contract** for
artifact placement, not just an illustrative tree.

- HTTP request/response DTOs belong in `api`.
- Transport adapters and controllers belong in `infrastructure`.
- Runtime/dispatch/logging framework classes belong in `engine`.
- Each concept implementation belongs in exactly one
  `concepts.<name>` package.
- Declarative sync classes belong in `syncs`.
- Flow tests belong in the `flows` test package under the configured
  test source root.

If a class fits none of those buckets, stop and justify a new package
explicitly instead of placing it ad hoc.

## Hard rules (machine-checked by `LegibleArchitectureRulesTest`)

- **R1 — no cross-concept imports.** A class in
  `concepts.X` must not import any class in `concepts.Y` (Y ≠ X). Syncs
  may reference any concept's `IRI` constant — that is the *only* legal
  cross-concept Java symbol.
- **R2 — one named graph per concept.** Each `*Concept` writes only to
  the named graph returned by `RdfVocabulary.conceptGraph("<name>")`.
  Cross-graph reads from another concept's named graph are forbidden.
- **R3 — syncs are declarative.** Classes in `syncs` may only have
  `final` fields and must coordinate exclusively via the SPARQL pattern
  in `whereClause()` / `thenBindings()`. No `if/else` on domain values,
  no I/O, no calls into concept classes.
- **R4 — `Web` is the sole HTTP entry.** Only classes inside
  `com.example.app.infrastructure` may carry Micronaut HTTP annotations
  (`@Controller`, `@Get`, `@Post`, …).
- **R5 — every concept is a `ConceptAgent`.** Every `*Concept` class
  inside `com.example.app.concepts` must be assignable to
  `com.example.app.engine.ConceptAgent`. This guarantees every action
  the concept performs is recorded in the action log against an
  addressable flow token.

## Method conventions

- A concept agent's `processInvocation(...)` method handles a single pending
  invocation and **must** call exactly one of `writeCompletion(...)` or
  `writeError(...)` before returning. Both helpers signal the
  `CompletionBus` automatically.
- A concept agent's `pollAll()` method enumerates every action name the
  concept handles, calling `pollAndProcess("<actionName>")` for each.
- A concept agent never reads from another concept's named graph and
  never calls another concept's class. Cross-concept information must
  arrive via `bindings` on an `ActionRecord`.
- A sync's `thenBindings()` must include exactly one
  `?_then_1 :concept <…> ; :name "…" ; :input [ … ] .` triple
  pattern. The base class parses this string to determine which
  concept's pending-invocation poll to schedule next tick — keep the
  format stable.
- Outcome values are uppercase string literals (e.g. `"OK"`, `"FOUND"`,
  `"GRANTED"`); concept actions write them as plain string literals via
  `ResourceFactory.createStringLiteral(...)`.

## SPARQL construction conventions (profile-specific)

These conventions apply only to this Java/Jena profile.

### Reserved variable names — MUST use exactly these names

The `SyncAgent` base class assembles `INSERT ... WHERE` around your
fragments. The outer shape binds these three variables:

| Variable | Purpose | Set by |
|---|---|---|
| `?_when_1` | The trigger action node (concept action that just completed) | Engine boilerplate `GRAPH` pattern |
| `?_flow` | The flow-token IRI shared across the causal chain | Engine boilerplate `GRAPH` pattern |
| `?_then_1` | The new downstream action node the sync creates | Engine `BIND(IRI(...))` |

**Your `whereClause()` and `thenBindings()` MUST use exactly these
three names when referring to the trigger action, flow token, and
new invocation.** NEVER use `?_w` for the trigger or `?_f` for the flow.
Other variables for request fields (`?_slug`, `?_token`, `?_userId`,
`?_root`, `?_ri`, `?_route`, etc.) are free-form.
If you use a different flow variable, the engine's `?_then_1 :flow
?_flow` INSERT will write the wrong flow token, and downstream
concepts / syncs will not match. If you use a different trigger
variable, the `FILTER NOT EXISTS { ?_when_1 :syncName [] }` dedup
guard will mark the wrong node, causing runaway re-firing.

```java
// Correct — uses the three reserved names
@Override
protected String whereClause() {
  return """
    ?_when_1 :concept <%s> ;
             :name    "getBySlug" ;
             :slug    ?_s .
    << ?_when_1 :outcome "FOUND" >> :flow ?_flow .
    ?_root :concept <%s> ;
           :name    "request" ;
           :input   ?_ri ;
           :flow    ?_flow .
    """.formatted(ArticleConcept.IRI, WEB_IRI);
}

// Wrong — uses custom names (?_fw, ?_myFlow). These are separate
// SPARQL variables from the engine's ?_when_1 / ?_flow.
?_fw :concept <%s> ; :name "lookup" ; :flow ?_myFlow .
```

### SPARQL-star outcome matching

CLAD uses RDF-star for outcome tracking. `ConceptAgent.writeCompletion`
writes BOTH a plain `:outcome` triple (to prevent reprocessing) AND an
RDF-star annotation (for sync matching). Sync `whereClause()` fragments
match the star annotation:

```java
// Correct — SPARQL-star pattern (matches the engine's annotation)
?_when_1 :concept <%s> ; :name "check" ; :userId ?_userId .
<< ?_when_1 :outcome "OK" >> :flow ?_flow .
```

The plain `:outcome` triple exists only to block reprocessing via
`FILTER NOT EXISTS { ?_action :outcome ?_any_outcome }` in
`ConceptAgent.findPendingInvocations()`. Syncs should never rely on
it — use the RDF-star form exclusively for outcome conditions.

Non-outcome field bindings (`:userId`, `:sessionToken`) are plain
triples on the action node.

### Sync fragment construction

- **Must filter by route.** Every sync that writes a `Web/respond` (or
  any action) based on a business-concept completion MUST include the
  root route in its `whereClause()`. Two syncs can fire on
  `Session/grant[GRANTED]` — one for login and one for register. Without
  a route filter, both fire for every flow. The pattern:
  ```java
  ?_root :concept <web> ; :name "request" ; :input ?_ri ; :flow ?_flow .
  ?_ri :route ?_route ; ...
  ```
  combined with `bindLiteral(sparql, "_route", "login")` in
  `parameterizeSparql`. Syncs that only fire on `Web/request` already
  have the route in their trigger — business-concept syncs MUST add it.
- **One invocation per sync firing.** `thenBindings()` must create
  exactly one `?_then_1` invocation.
- **Join via flow token.** Cross-concept coordination joins through
  action-log nodes that share `?_flow`; do not read another concept's
  named graph directly. Use only the engine's `?_flow` variable.
- **Keep outcomes explicit.** Match concrete outcome literals in
  `whereClause()` so each SPEC outcome maps to a distinct path.
- **Deterministic projection for reads.** In concept-side `SELECT`, only
  project fields you need and use `LIMIT 1` for singleton lookups.
- **Use ASK for existence checks.** Prefer `ASK` over `SELECT` when the
  caller needs only true/false.
- **Use text blocks for sync fragments.** All `whereClause()` and
  `thenBindings()` methods use Java text blocks (`"""..."""`) with
  `.formatted()` for IRI constants. Do not use `+` string concatenation
  with `\n` escapes in canonical sync classes.
- **Parameterize non-outcome string literals.** Route names, shared
  message strings, and similar discriminator literals are declared as
  `private static final String` constants and bound through
  `ParameterizedSparqlString`. In this profile, prefer overriding
  `parameterizeSparql(String sparql)` on `SyncAgent` rather than
  rebuilding the full outer update in each subclass.
- **Keep outcome literals inline.** Outcome values such as `"FOUND"`,
  `"OK"`, and `"GRANTED"` stay explicit in the fragment text so each
  branch remains visibly one-to-one with the approved SPEC outcome.

Quick examples:

```java
// Existence check: prefer ASK
boolean exists = actionLog.ask(
  "ASK { GRAPH <" + RdfVocabulary.conceptGraph("user") + "> { ?u :username \"ada\" } }"
);

// Singleton lookup: narrow SELECT with LIMIT 1
var rows = actionLog.select(
  "SELECT ?userId WHERE { GRAPH <" + RdfVocabulary.conceptGraph("user") + "> { " +
    "?u :username \"ada\" ; :userId ?userId . } } LIMIT 1"
);

// Sync whereClause: text block with formatted IRI and parameterized route literal
@Override
protected String whereClause() {
  return """
    ?_when_1 :concept <%s> ;
         :name    "request" ;
         :input   ?_inp ;
         :flow    ?_flow .
    ?_inp :route ?_route ;
        :copyId ?_copyId .
    """.formatted(WEB_IRI);
}

@Override
protected String parameterizeSparql(String sparql) {
  return bindLiteral(sparql, "_route", ROUTE);
}
```

## Constructor discipline

- Match what the tests instantiate: if tests call `new Account()`, the
  class must have a no-arg constructor. No constructor signature mismatch.
- No two constructors or methods with the same erasure (Java compile error).
- Prefer `HashMap` over `Map.of()` when entries must be added after
  construction — `Map.of()` returns an unmodifiable map.
- When the storage layer is configured, use it. Do not substitute an
  in-memory collection (e.g. `HashMap`) for the configured persistence
  technology.

## Tests

- `ConceptTestBase`, `SyncTestBase`, `FlowTestBase` in `src/test/java/com/example/app/`.
- Test classes mirror the production package they test.
- Stub tests (those waiting for a later sub-stage) are `@Disabled` with a `TODO` comment naming the sub-stage that will turn them on.
