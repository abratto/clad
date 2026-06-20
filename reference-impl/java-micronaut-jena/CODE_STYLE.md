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

- **Sync fragments, not full updates.** In `SyncAgent` subclasses,
  provide only `whereClause()` and `thenBindings()` fragments. The base
  class assembles `INSERT ... WHERE` and dedup logic.
- **Engine-owned variables are reserved.** Do not redefine `?_when_1`,
  `?_flow`, `?_then_1`, or `?_when_1`.
- **One invocation per sync firing.** `thenBindings()` must create
  exactly one `?_then_1` invocation.
- **Join via flow token.** Cross-concept coordination joins through
  action-log nodes that share `?_flow`; do not read another concept's
  named graph directly.
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

## Tests

- `ConceptTestBase`, `SyncTestBase`, `FlowTestBase` in `src/test/java/com/example/app/`.
- Test classes mirror the production package they test.
- Stub tests (those waiting for a later sub-stage) are `@Disabled` with a `TODO` comment naming the sub-stage that will turn them on.
