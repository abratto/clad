# Rmap conformance — CLAD's supported subset

CLAD realizes relational state with **Halpin's Rmap**, but it does not
implement every refinement in the published procedure. This file is the
authority for what CLAD does and does not derive. It exists so that
`rmap.py`, the Stage 03b data model, and the Stage 04a storage mapping tell
the same story.

- **Source:** Terry Halpin, *Object-Role Modeling: an overview*, §"Relational
  mapping" (ORM.net, 1997/2002); and *Information Modeling and Relational
  Databases* (Morgan Kaufmann, 2001/2008), ch. 11. See
  [`../reference/CITATIONS.md`](../reference/CITATIONS.md).
- **Implementation:** [`../../quality-gate/rmap.py`](../../quality-gate/rmap.py)
  is the single derivation. The input is the Stage 03b `## Conceptual model`
  block; the output is a migration and a runtime descriptor.
- **Procedure doctrine:** [`DATA_MODEL_NOTES.md`](DATA_MODEL_NOTES.md) for the
  CSDP steps; [`RELATIONAL_RMAP.md`](RELATIONAL_RMAP.md) for the pipeline;
  [`../implementation/STORAGE_MAPPING.md`](../implementation/STORAGE_MAPPING.md)
  for Stage 04a; the profile-specific rules live in
  [`../../reference-impl/java-micronaut/RELATIONAL_LOWERING.md`](../../reference-impl/java-micronaut/RELATIONAL_LOWERING.md).

## Halpin's stages and CLAD's adaptation

The overview presents a basic procedure; CLAD adapts it as follows.

| Halpin's stage | CLAD realization |
|---|---|
| Treat compositely identified objects as atomic; absorb subtypes into supertypes. | Compound subjects are realized as their own keyed table (a compidot). Subtypes are an **explicit per-model choice** (`absorb`, `separate`, or `partition`) rather than a single default; the chosen strategy must preserve the subtype constraints. |
| Map each composite-key fact type to a separate table keyed on that composite. | A `fact p : ( A, B ) -> V` becomes one table with `PRIMARY KEY (a, b)`. |
| Group simple-key facts attached to a common object type; use its identifier as the table key. | Simple facts with the same storage owner become columns on that owner's table, keyed on the owner's reference scheme. |
| Expand compositely identified objects into their identifying component attributes. | Compound subject components become the compidot's key columns. A reference *to* a compidot (a composite foreign key) is not expressible in the current grammar. |

CLAD's input is a **functional-fact profile** of ORM: each `fact` line names a
subject and a value. The author therefore supplies the grouping orientation.
CLAD does not re-derive a 1:1 fact type's orientation from both roles'
mandatory participation.

## Supported input subset

The Stage 03b block may use:

- `object-type E identified-by X` — an entity type and its reference scheme.
  `X` may be a value type, the entity's own identifier type (`EId`), or the
  intrinsic `E.id` scheme.
- `fact p : E -> V` — a simple fact type, with annotations `mandatory`,
  `optional`, `unique`, `unique while F absent`, `default`, and `in {…}`.
- `fact p : ( A, B ) -> V` — a compound (objectified) subject.
- `fact p : E -> { V }` — a multi-valued fact.
- `<Sub> is a <Sup> -- mapping: absorb | separate | partition`.
- `independent T` — an object type with no functional fact role.

Anything else is rejected by `verify_data_model.py` or by the derivation; it
is never silently dropped.

## Mapping rules and the semantics they preserve

| Conceptual form | Relational realization | Semantics preserved |
|---|---|---|
| Mandatory simple fact | `NOT NULL` column | Every instance of the subject has the value. |
| Optional simple fact | Nullable column | The value may be absent. |
| `value mandatory` / `value optional` | Role participation recorded; a 1:1 must be oriented on the mandatory side | The value role's participation is modelled and checked, not silently ignored. |
| `unique` | `UNIQUE` column | At most one subject per value. |
| `unique while F absent` | Partial unique index on `p` where `F IS NULL` | External uniqueness restricted to open individuals. |
| `unique ( p1, p2, ... )` | Table-level `UNIQUE (...)` | The predicate combination is unique within one table. |
| `unique (...) while F absent` | Partial unique index over the combination | The combination is unique among open rows. |
| Value constraint `in {…}` | `CHECK` | The column is restricted to the value set. |
| Compound subject | Compidot table keyed on the component columns | The individual *is* the component tuple. |
| Multi-valued fact | Child table keyed on `(subject, p)` | Zero or more values per subject. |
| `separate` subtype | Subtype table keyed on the supertype identity, with an intra-concept FK to the nearest ancestor table | A subtype row is a supertype row; membership is the existence of the subtype row. |
| `absorb` subtype | Subtype facts become **nullable** columns on the supertype table, with a membership `CHECK` | A non-member has all-guarded columns null; a member has every effective mandatory fact present. A mandatory subtype fact is not forced on unrelated supertype rows. |
| `absorb` + `discriminator p = v` | Membership is explicit: the supertype's `p` value selects the subtype; the check requires the subtype's mandatory facts when `p = v` and forbids its facts otherwise | Membership is decidable even when the subtype has only optional facts. |
| `disjoint ( A, B )` / `exhaustive ( Sup )` | Absorbed disjointness gets a pairwise `CHECK` when membership is inferable; partition is structural; separate-table disjointness/exhaustiveness is reported, not DB-enforced | The declared set constraint is either enforced or explicitly reported as unenforced. |
| `partition` subtype | The supertype's simple facts are flattened into each member's table; the supertype table is dropped | Membership is the member table; runtime writes are member-qualified. |
| Same-concept entity reference | `FOREIGN KEY` to the target's table **when the target has a data column** | An instance must reference an existing stored individual. |
| Identity-only target (no table, or only a primary key) | Opaque typed column, with a derivation warning | No referential integrity is enforceable because the target has no stored state. |
| Cross-concept identifier | Opaque typed column, never a FK | R2: concepts own isolated regions; syncs establish cross-concept meaning. |

### Type mapping

Built-in scalar names map as follows:

| Conceptual type | SQL type |
|---|---|
| `Int` / `Integer` | `INTEGER` |
| `Timestamp` / `Instant` | `TIMESTAMP` |
| `Boolean` | `BOOLEAN` |
| `Decimal` / `Numeric`, optionally `Decimal(12,2)` | `NUMERIC` / `NUMERIC(12,2)` |
| `UUID` | `UUID` |
| `Date` | `DATE` |
| `Time` | `TIME` |
| `Json` / `JSON` / `JSONB` | `JSONB` |
| `Bytes` / `Bytea` | `BYTEA` (base64 at the SPI boundary) |

Every other value type is a **domain value type** and defaults to `TEXT`
(rendered as `varchar` for jOOQ's `DDLDatabase`). Register a domain type in the
project `type map` to use a richer SQL type:

```
storage.type.Money=NUMERIC(12,2)
storage.type.Email=CITEXT
```

A feature-local `_config/type-map.md` overrides the root properties with
`Name=SQL` lines. `storage.type.strict=true` makes an unregistered value type
fail loudly instead of falling back to `TEXT`.

At runtime, `dev.legible.storage.ValueCodecs` provides built-in codecs for the
core SQL types and loads custom `ValueCodec` providers through `ServiceLoader`.
An SQL type with no codec fails loudly. Individual identifiers remain `TEXT`
columns because the engine's `Region` SPI addresses subjects as strings; the
richer types apply to fact values.

## Role-level participation

`mandatory` / `optional` describe the **subject** role; `value mandatory` /
`value optional` describe the **value** role. A 1:1 fact between two object
types must be oriented on the mandatory side (Halpin's grouping choice). CLAD
validates that orientation and rejects the optional-side form; it does not
auto-flip the predicate, because the runtime writes facts in the authored
subject→value direction. A mandatory value role on a non-1:1 fact is accepted
but reported as not enforceable by a single column.

## Multi-column uniqueness

`unique ( p1, p2, ... )` is a same-table constraint. The deriver maps every
predicate to one table and renders `UNIQUE (col1, col2, ...)`; the optional
`while F absent` form renders a partial unique index. Cross-table and
multi-valued predicates are rejected. Multi-column uniqueness is not a
substitute for a composite reference scheme: it constrains values, not
identity.

## Subtype-absorption semantics

`absorb` is the single-table strategy: subtype facts live on the supertype
table. It is only legal when membership is inferable from the data:

- The subtype must have **at least one mandatory simple fact** or a
  `discriminator` to act as the qualifier. A subtype with only optional facts
  and no discriminator has no decidable membership; use `separate`, add a
  mandatory fact, or add a discriminator.
- Every absorbed subtype fact is nullable on the supertype table.
- When the subtype has more than one guarded column, a `CHECK` enforces:
  **all guarded columns null (non-member)** or **all effective mandatory
  columns non-null (member)**. An optional subtype fact cannot appear without
  the mandatory set.
- Transitive absorbed chains include the effective mandatory facts of absorbed
  ancestors in the check, so a subtype member is also a valid member of each
  absorbed ancestor.
- An absorbed subtype fact cannot carry a `default` (the default would make
  non-members look like members).
- An absorbed subtype cannot own a multi-valued fact (conditional cardinality
  cannot be expressed without a discriminator); use `separate` or
  `partition`.
- A supertype cannot mix `absorb` and `partition` members, or `partition` and
  `separate` members: partition drops the supertype table that those
  strategies need.

For a subtype whose membership must be explicit and independent of its facts,
use `separate` — the subtype table is the membership record, and its FK
enforces the subset constraint. `separate` requires a supertype table to
reference; a supertype with no stored state is a modelling error, not a silent
missing FK.

## Entity-reference semantics

A fact value is an entity reference when it names either:

- a declared object type in the same concept, or
- a declared reference-scheme type of such an object type.

The resolver is concept-local. A type declared in another concept (or not
declared here) is a value type and stays opaque.

An FK is rendered only when the target's table has at least one **data
column**. The runtime writes facts as `predicate(subject) = value` and has no
"ensure this individual exists" operation, so a reference to an identity-only
table could never be satisfied. In that case the deriver keeps the column
opaque and warns; add a fact on the target (or model the value as a value
type) to obtain referential integrity.

Other target shapes are rejected rather than silently weakened:

- a **partitioned supertype** has no single table; reference a member instead;
- a **compidot** target needs a composite FK, which is outside this subset;
- an FK **cycle** between tables is not ordered automatically; break the cycle
  in the conceptual model.

A reference to an **absorbed subtype** resolves to the supertype table, so it
enforces supertype membership but not subtype membership. Use `separate` when
subtype membership must be enforced by the FK.

## Valid and invalid populations

These are the conformance examples the gate tests encode.

### Simple-key grouping

```
object-type UserId identified-by UserId
fact email : UserId -> Email -- mandatory, unique
fact displayName : UserId -> Name -- optional
```

Valid: one row per `UserId`; `email` non-null and unique; `display_name`
nullable.

### Compound subject

```
object-type Member identified-by Member
object-type Copy identified-by Copy
fact priority : ( Member, Copy ) -> Int -- optional
```

Valid: one row per `(member, copy)` pair; `priority` nullable.

### Absorbed subtype

```
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> PartyName -- mandatory
fact vatNumber : Employer -> VatNumber -- mandatory
fact payrollRef : Employer -> PayrollRef -- optional
Employer is a Party -- mapping: absorb
```

Valid: `party='p1', party_name='Ada', vat_number=NULL, payroll_ref=NULL`
(a non-employer); `party='p2', party_name='ACME', vat_number='VAT-1',
payroll_ref='PR-1'` (an employer).

Invalid: `party='p3', party_name='Solo', vat_number=NULL, payroll_ref='PR-3'`
(an optional subtype fact without the mandatory qualifier);
`party='p4', party_name='Half', vat_number='VAT-4', payroll_ref=NULL` is
**valid** (optional facts may be absent for a member).

### Entity reference

```
object-type Department identified-by DeptCode
object-type Employee identified-by Employee
fact deptName : Department -> Name -- mandatory
fact worksFor : Employee -> Department -- mandatory
```

Valid: `works_for` references an existing `dept_code`. Invalid: a `works_for`
value with no matching `Department` row (the FK rejects it).

### Identity-only target

```
object-type Member identified-by Member
object-type Loan identified-by Loan
fact borrower : Loan -> Member -- mandatory
```

The `Member` type declares no stored fact, so it owns no table. `borrower`
stays an opaque `TEXT` column and the derivation warns; the schema cannot
enforce that the member exists.

### Role-level 1:1 orientation

```
object-type Employee identified-by Employee
object-type Department identified-by DeptCode
fact employeeName : Employee -> Name -- mandatory
fact deptName : Department -> Name -- mandatory
fact manages : Employee -> Department -- mandatory, unique, value mandatory
```

Valid: one employee manages one department, and every department has a
manager. Invalid by derivation: the same fact written on the optional employee
side with `value mandatory` — the deriver requires the mandatory-side
orientation.

### Multi-column uniqueness

```
object-type User identified-by User
fact tenant : User -> Tenant -- mandatory
fact email : User -> Email -- mandatory
fact deletedAt : User -> Timestamp -- optional
unique ( tenant, email ) while deletedAt absent
```

Valid: `(t1, a@x)` open once; after soft-deleting that row, `(t1, a@x)` may be
opened again. Invalid: a second open `(t1, a@x)`.

### Discriminator and disjointness

```
object-type Party identified-by Party
object-type Employer identified-by Employer
fact partyName : Party -> Name -- mandatory
fact partyKind : Party -> PartyKind -- mandatory, in {individual, employer}
fact vatNumber : Employer -> VatNumber -- mandatory
Employer is a Party -- mapping: absorb, discriminator partyKind = employer
```

Valid: `partyKind = individual` with no VAT; `partyKind = employer` with a VAT.
Invalid: an individual with a VAT, or an employer without one. `disjoint ( A, B )`
adds a pairwise check for absorbed subtypes; `exhaustive ( Sup )` is inert for
partition and reported as unenforced for separate tables.

## Explicit non-goals

These are deliberate limitations, not silent gaps:

- **Automatic 1:1 predicate re-orientation.** Role participation is modelled
  and the mandatory-side orientation is enforced, but the deriver does not flip
  the authored subject/value direction in the runtime.
- **Cross-table disjoint/exhaustive enforcement.** Separate-table disjointness
  and exhaustiveness are declared and reported, not enforced by the generated
  schema; partition remains structural/inherent.
- General **subset, equality, and exclusion** constraints beyond FKs and the
  subtype strategies.
- **Derived facts → SQL views.** A `-- derived` fact is rejected by the
  Stage 03b check and by the derivation; it would otherwise be stored as a
  base column. Derived values are computed through approved actions, and no
  generated view path is added without a consumer.
- **Composite-reference and compidot-reference FKs.**
- N-ary fact types beyond a compound subject.
- **Typed identifiers / primary keys** and **arrays/custom domains** beyond the
  built-in scalar map and the `ValueCodec` registry. Identifiers remain `TEXT`
  because the engine SPI addresses subjects as strings.

## Why the subset is still faithful

The subset preserves the properties that make Rmap useful: elementary facts
map to normalized tables, keys come from reference schemes, uniqueness becomes
keys, mandatory facts become `NOT NULL`, value constraints become `CHECK`,
same-concept references become FKs when the target has state, and subtype
constraints are preserved as FKs (separate/partition) or qualified checks
(absorb). The unsupported items are the paper's advanced refinements, not the
basic mapping.

If a model needs a capability outside this subset, extend the grammar and the
derivation together, record the decision as a maintenance change, and add
valid/invalid population tests before claiming support.
