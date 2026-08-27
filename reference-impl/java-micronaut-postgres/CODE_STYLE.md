# Code style — `reference-impl/java-micronaut-postgres/`

Profile-specific conventions. The action-log engine is shared (`dev.clad.engine`);
this profile's own code is the concept-state persistence + app shape.

## Packages

```
com.example.app
├── infrastructure          WebController (sole HTTP entry; R4), DebugController
├── api                     DTOs for HTTP boundary + ResponseAssembler
├── concepts.<name>         Exactly one *Concept class; extends dev.clad.engine.ConceptAgent
├── syncs                   Declarative when/then rules (one final class per sync)
├── storage                 JooqFactory (ActionLog + DataSource + DSLContext + Flyway)
└── db                      JOOQ-generated tables (com.example.app.db, generated)

dev.clad.engine (shared clad-engine module)
└── ActionLog, FlowManager, ConceptAgent, SyncAgent, SyncDispatcher, … (shared)
```

## Concept-state conventions (JOOQ + Flyway)

- **State lives in Flyway migrations** under
  `src/main/resources/db/migration/V{n}__<table>.sql`. Quote
  identifiers lowercase (`"usernames"`) — the JOOQ `DDLDatabase` preserves
  quoted case, so quoted lowercase keeps Flyway (Postgres) and JOOQ codegen in
  agreement.
- **One schema per application** (`public`). Each table is named for the
  relation it holds, never the entity: `usernames`, `passwordauth_credentials`,
  `session_tokens`.
- **No FK crosses a concept boundary.** A column holding another concept's id is
  an opaque typed value (`user_id uuid`), never `REFERENCES`. Enforced by
  `verify_relational_mapping.py` (Stage 04a gate) and
  `LegibleArchitectureRulesTest.r2_no_cross_concept_table_access`.
- **Concepts access state only through their own JOOQ tables** (R2). A
  `UserNamingConcept` uses `USERNAMES`; it must never reference
  `PASSWORDAUTH_CREDENTIALS` or `SESSION_TOKENS`.
- **Identifiers are typed** (`uuid`). Concepts convert to/from `String` at the
  action boundary (`invocation.binding(...)` is a String literal).
- **Mandatory/optional** follow the Stage 03b model: `NOT NULL` for mandatory,
  nullable for optional, `DEFAULT` for defaults (see
  [`RELATIONAL_LOWERING.md`](RELATIONAL_LOWERING.md)).
- **Read-modify-write state is atomic.** A concept that reads then writes a row
  (e.g. `PasswordAuth.check` incrementing a failure counter) wraps the cycle in
  `dsl.transactionResult(...)` with `SELECT … FOR UPDATE` so concurrent
  invocations serialise on the row and cannot lose an update.

## Coordination is unchanged

Concepts extend `dev.clad.engine.ConceptAgent` and call `writeCompletion` /
`writeRefusal` / `writeError` with `RDFNode` outputs exactly as in the Jena
profile. The action log is in-memory RDF; only state persistence differs.

## Tests

- `PostgresConceptTestBase` starts a Testcontainers Postgres, runs Flyway, and
  provides a `DSLContext`; isolated concept tests use the test constructor
  `(ActionLog, CompletionBus, DSLContext)`.
- `TestPostgresDataSourceFactory` provides the `DataSource` bean for
  `@MicronautTest` flow tests.
- `LegibleArchitectureRulesTest` enforces R1 (no cross-concept imports),
  R2-relational (no cross-concept table access), R3, R4, R5.
