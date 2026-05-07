# Code style — `reference-impl/java-micronaut-jena/`

Profile-specific conventions. These do **not** apply to the
methodology folder; they exist because Java + Micronaut + Jena
imposes its own grain.

## Packages

```
com.example.app
├── engine                  Flow tokens, ActionLog, FlowManager, vocab
├── infrastructure          WebConcept (sole HTTP entry; R4)
├── api                     DTOs for HTTP boundary
├── concepts.<name>         Exactly one *Concept class per package
└── syncs                   Declarative when/then rules
```

## Hard rules (machine-checked by `LegibleArchitectureRulesTest`)

- **R1 — no cross-concept imports.** A class in
  `concepts.X` must not import any class in `concepts.Y` (Y ≠ X).
- **R2 — one persistence region per concept.** When the RDF backend
  lands, each concept owns one named graph. Today, each concept owns
  its in-memory state field directly; cross-concept reads are
  forbidden by R1.
- **R3 — syncs are declarative.** Classes in `syncs` may read flow
  tokens and call concept actions. They must not contain `if/else`
  branches on domain state, hold mutable fields, or do I/O.
- **R4 — `Web` is the sole HTTP entry.** Only `WebConcept` may carry
  Micronaut HTTP annotations (`@Controller`, `@Get`, `@Post`, …).
- **R5 — every action emits a flow token.** Every public method of a
  `*Concept` class must call `FlowManager.emit(...)` (heuristic check
  via bytecode method calls; concept methods that intentionally do not
  emit must be `private` or `protected`).

## Method conventions

- Public concept actions return an **outcome enum** declared next to the concept (`SessionOutcome`, `LoginOutcome`, …). They never return `null`.
- Concepts do not throw checked exceptions across the boundary; failure modes are outcomes.
- Flow-token field names live in `engine.RdfVocabulary` so syncs can pattern-match by stable identifier.

## Tests

- `ConceptTestBase`, `SyncTestBase`, `FlowTestBase` in `src/test/java/com/example/app/`.
- Test classes mirror the production package they test.
- Stub tests (those waiting for a later sub-stage) are `@Disabled` with a `TODO` comment naming the sub-stage that will turn them on.
