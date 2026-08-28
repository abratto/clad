# legible-engine

The canonical CLAD reference engine: a zero-dependency, storage-agnostic
runtime for concepts and syncs (`dev.legible.engine`).

## Semantics

- **Concept** — a state machine holding its own state in a `Region`
  (per-concept persistence region, R2). Actions are `Map execute(action,
  input)` returning an `outcome` plus named fields.
- **Sync** — a declarative `when`/`where`/`then` rule (`SyncRule`, pure
  data — no branching, R3). The `where` clause is evaluated by
  `WhereEvaluator` into *frames* (fan-out), supporting trigger/sibling joins,
  constants, concept-state reads (Pattern D), `OPTIONAL`, `bind(uuid)`, and
  `?_eachthen` grouping.
- **Fire-after-commit** — a completion is appended to the log *before* any
  sync is evaluated. There is no transaction and no rollback; a failing
  downstream action completes with a named `error` outcome.
- **Action log** — a per-flow append-only record store of `Invocation`s and
  `Completion`s, carrying provenance edges (`parentActionId`, `causedBySync`).
  Flows are archived (flushed to a sink + bounded buffer) at quiescence.
- **Concurrency** — per-flow log sharding; per-concept action serialisation
  (`SyncEngine.execute`); the archive buffer/sink are thread-safe.

## Components

| Component | Role |
|---|---|
| `FactStore` / `Region` | Storage SPI; one region per concept. `InMemoryFactStore` is canonical; `JenaFactStore`/`PostgresFactStore` live in `legible-storage`. |
| `ActionLog` / `InMemoryActionLog` | Append-only invocation+completion records. |
| `Concept` | The concept abstraction (map→map actions). |
| `SyncRule` / `Clause` / `Source` / `ThenInvocation` | The declarative `when/where/then` model. |
| `WhereEvaluator` | The `where`-clause binding engine (frames). |
| `SyncEngine` | Dispatch, commit, evaluate, mint; per-concept serialisation. |
| `FlowArchiver` / `FlowArchiveBuffer` / `FlowArchiveSink` | Bounded flow archival. |
| `DebugApi` | Introspection (the old `/api/dev/*` surface, as direct record lookups). |

See `methodology/architecture/ENGINE.md` for the full contract.
