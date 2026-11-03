# The relational pipeline — how CSDP facts become Postgres tables

This is the working map of CLAD's relational realization: what runs, in what
order, what each piece guarantees, and where every guarantee is proven. The
per-piece doctrine lives elsewhere and is referenced, not duplicated:

| Concern | Document |
|---|---|
| Conceptual (CSDP) modeling procedure | [`DATA_MODEL_NOTES.md`](DATA_MODEL_NOTES.md) |
| Conceptual-model block grammar | [`DATA_MODEL_NOTES.md`](DATA_MODEL_NOTES.md) §"The conceptual model block" |
| Storage mapping doctrine (per profile: relational / RDF / document) | [`../implementation/STORAGE_MAPPING.md`](../implementation/STORAGE_MAPPING.md) |
| Profile-specific lowering rules (constraints, subtypes, migrations) | [`reference-impl/java-micronaut/RELATIONAL_LOWERING.md`](../../reference-impl/java-micronaut/RELATIONAL_LOWERING.md) |
| Maintenance records for each refinement | [`../..`/maintenance/](../../maintenance/) (`rmap-table-set-storage.md`, `csdp-machine-model-to-rmap.md`, `relational-gaps-closure.md`) |

## The pipeline at a glance

```
Stage 02 concept spec               Stage 03b (CSDP, canonical)           workflow (Python)
--------------------                ---------------------------           ----------------
## State (relational)  ─generate──▶ <Name>.data-model.md                  quality-gate/rmap.py
   notation                           + ## Conceptual model  ─parse──▶ derive RmapModel
                                                                          │
(generate_data_model.py   verify_data_model.py requires + checks         ├─▶ V<n>__*.sql (Flyway)
 deterministically;       the block; humans resolve the judgment         └─▶ _generated/rmap-schema.json
 judgement steps are      steps)
 skeleton + <TODO>)

                                                                             runtime (Java)
                                                                             ---------------
                                                                             RmapPostgresFactStore
                                                                             reads the generated descriptor;
                                                                             Flyway owns DDL
```

The `## State` notation remains the concept's *authored* state and the
generator's input; the 03b `## Conceptual model` block (a faithful transcription
of the same facts, plus reference-scheme declarations) is the **canonical
machine input** to Rmap. `verify_data_model.py` checks the block against
`## State`; `quality-gate/rmap.py` is the single Rmap implementation.

**Java is an implementation target, not a generator.** Java consumes the
generated SQL migration and runtime schema descriptor. It does not derive,
validate, or render workflow artefacts.

## What a concept derives to (the rules)

**Table sets.** A concept region is one table when its facts range over one
object type, and a *table set* (`RmapModel`) otherwise: one table per object
type, one compidot per objectified (compound) subject, one child table per
multi-valued fact.

| Machine-model clause | Realisation |
|---|---|
| `fact p : S -> V` mandatory / optional / `-- default d` / `-- in {…}` | typed column on `S`'s table; `NOT NULL` / nullable; `DEFAULT d`; `CHECK` |
| `fact p : S -> V -- unique` | column `UNIQUE` (or the subject's `PRIMARY KEY`) |
| `fact p : S -> V -- unique while F absent` | **partial unique index** `(p) WHERE F IS NULL` replacing the plain `UNIQUE` — external uniqueness over open individuals (e.g. at most one *open* loan per copy) |
| `fact p : (A, B…) -> V` | compidot table, `PRIMARY KEY (a, b…)` — the individual *is* the component pair; no surrogate id, no mapping table |
| `fact p : S -> { V }` | child table `PRIMARY KEY (s, p)` |
| `Sub is a Sup -- mapping: separate` (default) | member table keyed on the supertype's identity column + rendered intra-concept `FOREIGN KEY` |
| `Sub is a Sup -- mapping: absorb` | subtype facts become nullable columns on the supertype's table |
| `Sub is a Sup -- mapping: partition` | derivation realises it (flattening, no parent table); **runtime-writable via member-qualified operations** — plain operations on shared predicates throw naming the members; see guardrails |
| `independent T` | single-column table keyed on `T`'s reference scheme |
| cross-concept identifier | opaque typed column — never a foreign key (R2) |
| role membership (your "PartyRole" discriminator) | not a subtype mapping at all: assert the objectified membership fact (`member : (Party, Role) -> Timestamp -- mandatory`) beside a role catalog — that derives the junction table with the discriminator pair as its PK |

Type mapping: `Int`/`Integer` → `INTEGER`; `Timestamp`/`Instant` →
`TIMESTAMP` (values round-trip as ISO-8601 instants); `Boolean` → `BOOLEAN`;
everything else `TEXT`.

## Runtime write semantics (why the schema can be strict)

The `Region` SPI writes one fact per call, yet the schema honours Rmap's
mandatory→`NOT NULL`. The piece that makes this sound is the **transactional
region**: `SyncEngine.execute` wraps each concept action in
`beginAction()`/`flushAction()` (`TransactionalRegion`). A durable region
buffers the action's writes and flushes them as one statement per individual —
mandatory columns of one row arrive together. Three consequences worth
knowing cold:

1. **A retry re-supplies everything.** `abortAction()` empties the buffer; after
   a failed flush (e.g. an out-of-enum `CHECK` violation), the next action must
   assert the individual's full mandatory fact set again — nothing partial
   survives.
2. **Single-fact writes outside an action update in place.** A lone `write` on
   an existing row(touches only its column) — never an `INSERT … ON CONFLICT`
   upsert: PostgreSQL validates `NOT NULL` on the *proposed insert tuple before*
   resolving the conflict, so partial upserts of mandatory rows would fail
   spuriously. When a fact's column is part of a composite key (multi-valued),
   inserting-if-absent honoured the full-key identity instead of overwriting a
   sibling.
3. **Retracts have three shapes.** Retract a mandatory fact without a default
   or a key component → the row is deleted (the individual ceases). Retract a
   resettable fact → reset to its Rmap `DEFAULT`. Retract a multi-valued child
   fact → the child rows go. Retract an *optional objectified* fact (a compidot
   whose value optional) → the value NULLs but the keyed row persists
   (`RmapEdgeBehaviorTest` P5 pins this contrast).

## Guardrails (fail loudly, by design)

- **Unparseable state/block clauses throw** at derivation — no silent drop.
- **Partition is member-addressed.** A plain operation on a flattened
  (multi-owner) predicate throws at operation time, naming the members;
  member-qualified operations (`write(member, subject, predicate, value)`)
  route to the member's own table — which is what makes a partitioned
  region, including its mandatory flattened predicates, writable. The
  member qualifier may also name a `separate` subtype or the supertype
  itself (each routes to its own table); an absorbed member has no table
  and fails loudly. The role-catalog recipe above remains the modelling
  alternative (membership as an objectified fact).
- **Foreign keys render and enforce.** A `separate` subtype write for an
  individual with no supertype row fails on the FK — the fact model's own
  `Sub is a Sup` subset constraint. There is no implicit base-row
  materializer; the concept action writes the supertype's facts.
- **Child-table FKs are gated.** A multi-valued child's FK references the
  table actually keyed on its subject, but is omitted when that table is
  identity-only (carries no facts — it could never hold a row). Model such
  membership with the role-catalog recipe instead.
- **The in-memory store implements none of the constraints** (FK, `NOT NULL`,
  `CHECK`, filtered uniqueness). Enforcement is the durable profile's
  contract; `InMemoryFactStore` implements the SPI semantics (composite
  prefix reads, absence-as-empty) only.

## Schema ownership and the drift guard

**Flyway owns DDL.** `quality-gate/rmap.py` renders the derived model set into
a versioned migration (`V1__login_rmap.sql` in the shipped profile); the
runtime store never creates tables in deployment
(`RmapPostgresFactStore.createSchema()` is the dev/test helper). jOOQ's code
generator (`DDLDatabase`) introspects the committed migration into typed
classes.

The drift guard is `./clad rmap --check`: it regenerates the migration from the
conceptual model and fails when the committed file is stale. Regenerate with
`./clad rmap --write <migration-path>` (add `--force` deliberately when
overwriting a migration that may already be applied — the guard refuses a
silent rewrite).

**Project aggregate and incremental migrations.** A multi-feature app has one
current model per canonical concept, not one migration per feature:

```
# one combined runtime descriptor from the canonical corpus
python3 quality-gate/rmap.py --features-dir features --app-label app   --json app/src/main/resources/rmap-schema.json

# incremental DDL from a deployed baseline descriptor
python3 quality-gate/rmap.py --features-dir features   --baseline deployed-rmap-schema.json   --alter app/src/main/resources/db/migration/V2__add_tagging.sql
```

The incremental mode emits `CREATE TABLE` for new tables and `ALTER TABLE ADD
COLUMN/CONSTRAINT` for additions; it never drops tables or columns
automatically (they are reported for review), and it refuses a new mandatory
column without a default. This is the production path for a schema change;
regenerating a base migration is only for an undeployed app.

**Baseline discovery.** Record the deployed descriptor once:

```
python3 quality-gate/rmap.py --features-dir features \
  --record-baseline prod
```

`--alter` then finds it automatically: an explicit `--baseline <name-or-path>`
(the path may be a deployed descriptor such as `deployed-rmap-schema.json`), the
`rmap.baseline` property (feature-local `_config/rmap.baseline.md` wins), or
the default `_generated/rmap-baselines/default.json` under the repo root (also
searches `_system/rmap-baselines/` and the feature's `_generated/`). Codegen caveat: `DDLDatabase` is an H2
parser; a partial unique index may not parse — the shipped login migration
carries none, and an app adopting filtered uniqueness must re-verify its
codegen step (see `RELATIONAL_LOWERING.md`).

## Runtime realizations (profiles)

| Binding | Concept state | Notes |
|---|---|---|
| `java-legible` (canonical teaching profile) | `InMemoryFactStore` | no transport framework at all |
| `java-micronaut` default | `InMemoryFactStore` | full HTTP stack, zero database |
| `java-micronaut` `clad.storage=postgres` | `RmapPostgresFactStore` | Flyway + jOOQ; CI `postgres-verify` runs its Testcontainers suite |
| `java-plain` (any `DATABASE_URL`) | `RmapPostgresFactStore` | plain `main()`: Flyway → derived store → `LoginApp`; **no transport framework** — HTTP is the adopter's choice |

An action log remains in-memory in every binding; an RDF/JSON-LD backend is
guidance, not a shipped profile (`STORAGE_MAPPING.md`; see also its JSON-LD
position: interchange/adapter surface, not a third durable path without a
consumer).

## Where each guarantee is proven

| Guarantee | Proof |
|---|---|
| `## State` ≡ conceptual model (no silent divergence) | `quality-gate/verify_data_model.py` fidelity check |
| Derivation correctness across shapes | `quality-gate/tests/test_rmap.py` (single, table-set, compound, multi, subtype×3, independent, filtered) + byte-frozen migration oracles |
| Derivation survives real files, not strings | `test_machine_model_parser.py` + `test_rmap.py` parity tests |
| Postgres round-trips per domain | `RmapDomainStorageTest` (clinic 3-part objectified, ordering child tables/defaults, PatientRegistry separate-subtype join, lending loans) |
| Guardrails are behaviour, not comments | `RmapEdgeBehaviorTest` P1–P5 (loud FK, CHECK rejection & retry semantics, partition member-addressing, filtered-vs-plain uniqueness, retract shapes) |
| Schema ≡ committed migration | `./clad rmap --check` (Python) + `RmapPostgresPersistenceTest` (Flyway owned, jOOQ agrees) |
| Pipeline end-to-end on the shipped app | CI `postgres-verify`: `mvn verify -pl legible-storage,java-micronaut -am -Dclad.storage=postgres` |

## Worked examples to read

- **Login trio** — `examples/UC-00-login/stages/03b_data-model/output/*.data-model.md`
  (conceptual blocks), `_generated/rmap-schema.json` (runtime descriptor), and
  `reference-impl/legible-storage/…/LoginSchemas.java` (loads the descriptor).
- **Shape coverage** — `reference-impl/legible-storage/src/test/resources/domains/`
  (`clinic`, `ordering`, `lending`): each concept ships its `## State`, the
  resolved 03b data model, and the frozen migration oracle.
