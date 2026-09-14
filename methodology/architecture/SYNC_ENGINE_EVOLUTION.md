# How CLAD's sync implementation evolved

Three engine generations sit behind the single `when/where/then` sync
discipline this methodology teaches. Reading them in order explains
artefacts agents still meet in the tree — retired hard rules, the
`maintenance/` records named in commit history, and the vocabulary in
older files like `RELATIONAL_LOWERING.md` — and why the current engine is
the shape it is.

## 1. Sync-as-transaction (2025, `dev.clad.engine`)

The first engine encoded the *older* reading of Jackson's *The Essence of
Software*: a sync and the concept action it calls happen inside one
atomic transaction.

- `ConceptAgent.writeCompletion` performed an **atomic composite write** —
  the completion plus the downstream sync invocations inside a single Jena
  transaction with `abortBatch` rollback.
- Syncs were **SPARQL-over-RDF**: a `SyncAgent` subclass lowered its
  `when`/`where`/`then` into SPARQL `SELECT`/`UPDATE` against per-concept
  RDF named graphs; `ASK` predicates acted as guards; the concept state
  was the graph store itself.
- Marker vocabulary that still exists: `ActionLog`, `ConceptAgent`,
  `SyncAgent`, `SyncDispatcher`, `FlowManager`, RDF-star action triples.
- Hard rules **R10 (SPARQL reserved variables)** and **R21
  (RDF-star programmatic construction)** are the scars of this engine —
  both now retired with notes in [`implementation/RULES.md`](../implementation/RULES.md).

The stack was retired in v0.5.0: `reference-impl/clad-engine/` and
`reference-impl/java-micronaut-jena/` are no longer in the build or any
quality-gate check, and receive no maintenance; the last version containing
them is tag `v0.4.0` (see
[`reference-impl/LEGACY.md`](../../reference-impl/LEGACY.md)).
`reference-impl/java-micronaut-postgres` was re-lowered off it in v0.3.5
(see `maintenance/reference-profiles-fire-after-commit.md`).

## 2. Fire-after-commit (v0.3.2, `dev.legible.engine`)

Following the paper's own direction — Eagon Meng's sync DSL "gets rid of
the need for transactions, and also allows much finer granularity"
(arXiv:2508.14511 / 2606.11051) — the engine was re-architected so that:

- **the action is the atomic unit**: a concept mutates only its own
  `Region` of the shared `FactStore` SPI (in-memory, Jena, or Postgres —
  `reference-impl/legible-storage/` proves storage-agnosticism);
- **syncs fire after commit**: the per-flow action log
  (`Invocation`/`Completion` with `parent`/`causedBySync` lineage) is the
  source of truth; a downstream failure is a named `outcome`, not an
  exception to roll back;
- the `where` clause is a **declarative frame binder** — `Bind`/`FanOut`/
  `Guard`/`Optional` clauses over trigger/sibling/completion/state sources,
  with `?_eachthen` grouping ('frames model', matching the paper's
  `Frames`/`collectAs` intent while keeping `where` code-free).

`reference-impl/clad-engine/` retains the retiring machinery;
`maintenance/fire-after-commit-engine.md` records the change itself.

## 3. Paper-faithful when-matching

> **Release-order note:** this change was tagged `v0.3.6`, but it landed on
> `main` after the parallel `v0.4.0`/`v0.5.0` simplification releases
> (grammar normalization + legacy retirement) and is content on the
> v0.5.0-or-later tree. Versions remain immutable tags; the changelog is
> the sequencing reference.

The last parity step with the paper authors' own reference
implementation (MIT 61040 conceptbox, `implementing-synchronizations.md`):

- **`SyncRule` gained an optional input-value matcher on the trigger** —
  `when Web/request (route: "profile") : routed` — so dispatch on flow
  identity moved from hand-written `where`-guards (`R15`) into the
  `when` token, exactly as the reference implementation models it.
- `Guard` remains for comparisons a literal matcher cannot express
  (non-literal operands).
- Two deltas against conceptbox stay **deliberate divergences** (no
  imperative `where` filters or JSON assembly — R3; rich query-actions in
  `where` — deferred), recorded in
  [`maintenance/engine-when-input-matching.md`](../../maintenance/engine-when-input-matching.md)
  and [`SYNC_PATTERNS.md`](SYNC_PATTERNS.md)
  (`SYNCHRONIZATIONS.md` §"Input matching in the when clause").

## Standing comparison to the reference implementation

| Capability | conceptbox (paper authors) | CLAD engine |
|---|---|---|
| when/where/then record per sync | yes (`*.sync.ts`) | yes (`*.sync.md` + `SyncRule`) |
| when-matching on input values | yes (`actions[...,{path:"/X"}]`) | yes since v0.3.6 (`inputPattern`) |
| in-`where` imperative filters / JSON assembly | yes | **no — deliberate divergence** (R3) |
| concept query actions as where sources (`_getByTarget`) | yes | deferred (non-goal, record of v0.3.6) |
| route guards | implicit in when-pattern matches | `Guard` remains for non-literal comparisons (R15) |
| `?_eachthen` grouping | `collectAs` | parity (grouped dedup) |
| OPTIONAL | — | CLAD superset |
| per-concept permutations | — | FanOut/StateRead (R-map aware) |
| flow lineage `parent`/`causedBySync`, archiving, `/api/dev/*` debug, replay | partial (multi-when flow history only) | CLAD superset |
| durable concept state | in-memory only | `FactStore` SPI (in-memory/Jena/Postgres) |
| multi-`when` join declarative | direct | idiom: trigger + `SiblingInput`/`SiblingField` in the same flow |
