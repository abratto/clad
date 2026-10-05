# Relational lowering — Stage 03b data model → Postgres schema

The deterministic contract for mapping an approved Stage 03b conceptual data
model into this profile's relational schema. Sync lowering is handled by the declarative `SyncRule` model shared with
the canonical profile.

## Source of truth

Stage 03b produces a profile-neutral CSDP fact model (Halpin's ORM tradition —
see `methodology/architecture/DATA_MODEL_NOTES.md`). Its relational mapping is
Halpin's **Rmap**: a fact type becomes either an absorbed column or a separate
table, decided by **arity**, the **uniqueness constraint**, and **mandatory
roles**. CLAD adds one constraint of its own: **no cross-concept foreign key**.

## The mapping rules

| Stage 03b form | Relational realization |
|---|---|
| `fact p : S -> V` (mandatory) | column on S's table, `NOT NULL` (a `TransactionalRegion` flushes one individual's writes as one statement) |
| `fact p : S -> V` (optional) | column on S's table, nullable |
| `fact p : S -> V` with a default | column with a `DEFAULT` |
| `fact p : S -> { V }` / "zero or more" | child table, composite PK `(subject, p)`, intra-concept FK to S's table |
| `fact p : ( A, B ) -> V` (objectified subject) | compidot table keyed on the component columns — no surrogate id |
| value constraint (e.g. `in {…}`) | `CHECK` constraint |
| uniqueness constraint | `UNIQUE` (or `PRIMARY KEY` on the subject column) |
| filtered uniqueness: `unique while <field> absent` | partial unique index — `(col) WHERE <field> IS NULL` — replacing the plain `UNIQUE`; external uniqueness over open individuals, which preserves 1:1-with-history (a returned loan frees the copy) |
| intra-concept reference | `FOREIGN KEY (col) REFERENCES table(col)` — rendered by both DDL writers; child-table FKs name the parent keyed on the fact's subject, and are omitted when that table is identity-only (it could never hold a row) |
| intra-concept entity reference | real FK (same concept) |
| **cross-concept identifier** | **opaque typed column — never a FK** |

### Worked example — the three UC-00-login concepts

```
User:        username: UserId -> String            (mandatory, unique)
PasswordAuth: passwordHash: UserId -> PasswordHash  (mandatory)
              failedAttempts: UserId -> Int         (mandatory, default 0)
              lockedUntil: UserId -> Timestamp      (optional)
Session:     token -> UserId                        (via grant)
```

```sql
CREATE TABLE "usernames" (
    "user_id"   uuid PRIMARY KEY,
    "username"  varchar(255) NOT NULL UNIQUE
);
CREATE TABLE "passwordauth_credentials" (
    "user_id"         uuid PRIMARY KEY,     -- opaque; NO FK to usernames
    "password_hash"   text NOT NULL,
    "failed_attempts" int  NOT NULL DEFAULT 0,
    "locked_until"    timestamptz NULL
);
CREATE TABLE "session_tokens" (
    "session_token" uuid PRIMARY KEY,
    "user_id"       uuid NOT NULL           -- opaque; NO FK
);
```

`user_id` appears in three concepts' tables as an opaque value. No foreign key
crosses a concept boundary — that is R2 ("one storage region per concept, no
cross-region reads") expressed at the DDL level.

## Schema-per-application + relation-named tables

One application schema (default `public`); each concept owns its own table.
The table is named for the **relation** it holds (`usernames`,
`passwordauth_credentials`, `session_tokens`) — never for the entity
(`user_accounts`), which invites the "one big entity table" conflation Jackson
warns against. The individual identity (`user_id`) is the key; ownership is
enforced structurally:

- **No two concepts reference the same table** (`LegibleArchitectureRulesTest.r2_no_cross_concept_table_access`).
- **No FK crosses a concept boundary** (`verify_relational_mapping.py`).

## Constraint realization

- **Uniqueness** → `UNIQUE` / `PRIMARY KEY`.
- **Mandatory** → `NOT NULL`.
- **Optional** → nullable column.
- **Value constraints** → `CHECK`.
- **Set/subset** → FK (intra-concept only).

## Subtypes and independent object types

Two further R-mapping refinements are realised by the same derivation
(`dev.legible.storage.RmapDeriver`); the machine-model block expresses the
structure, not the mapping choice — the mapping choice is a per-model decision
recorded in the fact line:

| Stage 03b form | Relational realisation |
|---|---|
| `Sub is a Sup -- mapping: absorb` | The subtype's simple-key fact types become columns on the supertype's table (the subtype itself realises no table). Right for small/sparse subtypes: no extra join, subtype columns nullable where their supertype sibling is optional. |
| `Sub is a Sup -- mapping: separate` (or no mapping declared — the deterministic default) | The subtype gets its own table keyed on the **supertype's identity column** (a subtype has no reference scheme of its own; a subtype row is a supertype row), with a rendered intra-concept FK naming the supertype's table. **Write semantics:** the FK is the fact model's own subset constraint — a subtype fact for an individual with no supertype row fails loudly, so a concept action creating a subtype individual writes the supertype's facts in the same buffered action. Nothing materializes the base row implicitly. |
| `Sub is a Sup -- mapping: partition` (disjoint, exhaustive) | The supertype's own fact types are flattened into each member's table at derivation. **Not runtime-routable:** the region SPI routes facts by predicate to the first owning table, and partition puts the same predicate in every member, so the store refuses such a region at creation (naming the shared predicates). Derivation still realises the schema for documentation; a concept wanting partition runtime must model `separate` (default)/`absorb`, or extend the SPI with member-addressed writes (a gated decision). |
| `independent T` | A single-column table keyed on `T`'s reference scheme, beside the concept's other tables (`concept__t`), for object types that play no functional fact role ("just in case a model needs them"). |

**Codegen note:** the partial unique index (`WHERE … IS NULL`) is standard on
Postgres but may not be parsed by jOOQ's `DDLDatabase` (H2); the shipped login
migration carries none. A derived app adopting filtered uniqueness must
re-verify its codegen step.

`RmapDeriver.deriveFromDataModel()` still throws when a concept realises as more
than one table — callers with multi-table regions use
`deriveModelFromDataModel(...)`.

## Deferred: derived facts → SQL views

Deliberately **tabled** during the P-series (recorded here so the deferral is
a decision, not a gap). Every derived value in the current state space is
derived at concept-read time through an approved action — `context` (the
ordered turn concatenation), `matchScore`, queue wait time, analytics summary
counts — and every consumer of derived state reads through the concept layer
(completions and the `Region` SPI). Nothing reads the store directly by SQL.

Generating SQL views now would (a) add a second read path that bypasses the
concept layer, (b) require a derivation notation the approved `## State`
blocks do not carry, and (c) produce schema surface with no consumer. If a
third-party consumer (e.g. BI) ever needs direct SQL, a generated view is the
adapter boundary for it — that would be a new, properly gated decision with
an actual consumer, not unprompted scheme building.


## Schema versioning — Flyway owns DDL

When an R-map/SQL store is used, **Flyway owns the schema (DDL)**. The base
migration `src/main/resources/db/migration/V1__login_rmap.sql` is **generated**
from the same R-map derivation the runtime store reads
(`dev.legible.storage.RmapMigration` over `LoginSchemas`), so it cannot drift
from the concepts:

- **Applied at startup** by `store.postgres.StoreInitializer`
  (`Flyway.migrate()`); the runtime store does **not** create tables
  (`RmapPostgresFactStore.createSchema()` is a dev/test helper only).
- **jOOQ codegen introspects the migration** (`jooq-codegen-maven` + `DDLDatabase`
  over `db/migration` → `com.example.app.db`), so the generated tables track
  the versioned schema.
- **Drift guard:** `RmapMigrationTest` fails when the committed migration is
  stale. Regenerate after any concept data-model (machine-model block) change:

  ```
  mvn -f reference-impl/pom.xml -pl java-micronaut -am test \
      -Dtest=RmapMigrationTest -Drmap.migration.write=true
  ```

`TEXT` is rendered as `varchar` so jOOQ's `DDLDatabase` (H2) can parse it;
the types are equivalent on Postgres. Later schema changes are new `Vn`
migrations (Flyway is append-only after release) — author them at Stage 04a
from the changed data model.

## Seeding

Keep **schema/reference data** and **demo/fixture data** separate:

- **Reference/lookup data** (enums, static tables) → Flyway, as a versioned or
  repeatable (`R__*.sql`) migration.
- **Demo/fixture data** (the `ada` user) → **not** a production migration. It is
  seeded by the app's `DemoSeed` through the engine's `FactStore` SPI, so it
  works identically on the in-memory binding (which has no Flyway) and does not
  ship demo rows to production. If a durable-only dev seed is ever wanted, add
  it under a separate Flyway `locations` (e.g. `classpath:db/dev`) gated by an
  environment property — never in the base migration.

## Traceability

The mapping must stay traceable to the approved Stage 03b elementary facts —
Stage 04a must not invent new facts, fields, or constraints. If a fact type
cannot be mapped without inventing structure, repair the conceptual model first,
exactly as `methodology/implementation/STORAGE_MAPPING.md` requires.
