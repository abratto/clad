# Data model notes — drafting per-concept conceptual data models

CLAD's Stage 03b derives a **profile-neutral conceptual data model**
from each concept's approved `state` section and any approved concept-state
exposure from coordination review. This file is the procedural reference
for that work: how to turn prose state into elementary facts, fact
types, and constraints without smuggling in storage decisions.

The procedure is adapted from the CSDP described by Terry Halpin and
the ORM tradition summarized by Mustafa Jarrar. CLAD does **not** adopt
full ORM-ML syntax, but it should stay recognizably faithful to the
seven-step CSDP. See [`../reference/CITATIONS.md`](../reference/CITATIONS.md).

## When this file applies

Stage 03b only.

## Fidelity statement

CLAD adopts the **seven-step structure** of the CSDP and a simplified
textual rendering of its outputs. It does not require ORM diagrams or
ORM-ML XML, but the `03b` artifact should still make the following
classes of decision explicit when they arise:

- elementary facts
- object/value typing
- fact types
- uniqueness constraints
- mandatory role constraints
- value constraints
- set-comparison constraints
- subtype constraints
- derivations
- final consistency checks

## The seven CSDP steps

For each concept independently — never model two concepts together.

### Step 1 — Transform familiar information examples into elementary facts, and apply quality checks

Start from familiar examples grounded in the approved concept `state`
section. Write a few concrete example sentences in natural language.
Then verbalize those examples as **elementary facts**.

Quality checks:

- Are objects and values identified clearly?
- Does any sentence need to be split into simpler facts?
- Does any pair of facts need recombining because the split lost meaning?

### Step 2 — Draw a draft diagram of the fact types and apply a population check

CLAD uses prose rather than a graphical ORM diagram here, but the
artifact must still name:

- object types
- value types
- fact types

Then apply a population check: confirm that at least one familiar
example populates each fact type.

### Step 3 — Check for entity types that should be combined, and note any arithmetic derivations

Check whether two provisional entity types should really collapse into
one conceptual type. Also note any arithmetic derivations such as
counts, sums, or other quantity facts that are derivable from more
primitive facts and therefore should not be treated as stored base
facts.

### Step 4 — Add uniqueness constraints, and check arity of fact types

Record uniqueness constraints explicitly and check arity. If a fact type
contains hidden functional dependencies or should really split into
multiple simpler fact types, do that here.

### Step 5 — Add mandatory role constraints, and check for logical derivations

Record mandatory roles explicitly. Then check for logical derivations:
facts derivable from other facts without arithmetic. Such facts should
be marked derived rather than modeled as stored base facts.

### Step 6 — Add any value, set comparison, and subtyping constraints

When they arise, make these explicit:

- value constraints
- subset / equality / exclusion constraints
- subtype constraints

If a category is not needed for a concept, say so explicitly.

### Step 7 — Add other constraints and perform final checks

Capture any remaining constraints that do not fit the earlier classes,
then run final checks for:

- consistency with the approved concept state
- consistency with approved concept-state read exposure from 03a
- avoidable redundancy
- completeness of the conceptual model for this concept

## Cross-concept rule

Do not model foreign keys or direct region-sharing across concepts. If a
concept carries another concept's identifier, it is an opaque value
whose runtime meaning is established by syncs, not by a schema-level
relationship.

## The machine model block

The seven CSDP steps above are the human-facing model. A relational profile
realizes them via Halpin's Rmap, so the data model also carries a small,
hand-authorable **machine model** block that Rmap consumes directly. It is a
faithful transcription of the same elementary facts and constraints the steps
name — never a new decision. It is generated deterministically by
`quality-gate/generate_data_model.py` from the concept `## State` relations and
validated by `quality-gate/verify_data_model.py`.

CLAD deliberately does **not** use Jarrar/Demey/Meersman's ORM-ML here:
ORM-ML is an XML serialization of the ORM *diagram* (object roles referenced by
id), defined by an external XML Schema, and is explicitly "not meant to be
written by hand or interpreted by humans." CLAD adopts the CSDP *step structure
and constraint vocabulary* and a compact textual rendering of the subset Rmap
consumes (fact types and arity, reference schemes, uniqueness, mandatory roles,
value constraints, subtyping).

Grammar (one clause per line; `#` starts a comment; blank lines ignored):

```
## Machine model

object-type <EntityType> identified-by <IdType>
fact <predicate> : <EntityType> -> <ValueType> -- <annotations>
fact <predicate> : ( <A>, <B> ) -> <ValueType> -- <annotations>
fact <predicate> : <EntityType> -> { <ValueType> } -- <annotations>
<Sub> is a <Sup> -- mapping: absorb | separate | partition
independent <ObjectType>
```

- `object-type` declares an entity type and its reference scheme (the fact
  that identifies it). A value type is never declared as an object type.
- `fact` is one elementary fact type. `( A, B )` is a compound (objectified)
  subject; `{ V }` is a multi-valued ("zero or more") fact.
- `<annotations>` is the same `--` tail the `## State` notation uses:
  `mandatory` | `optional`, `unique …`, `default <expr>`, `in {a, b, c}` or
  `in {a..b}`.
- `is a` declares a subtype and the per-model Rmap mapping (default
  `separate`); `independent T` declares an object type with no functional role.

Rules:
- Exactly one `## Machine model` block per data model.
- Every object type in a `fact` subject must be declared with `object-type`
  (or be a value type introduced by `->`); the block must not introduce facts
  absent from Steps 2/4/5.
- No storage construct may appear in the block (no SQL types, `FOREIGN KEY`,
  table names) — the block is conceptual, like the rest of the artifact.

## Output shape

Write the result to `output/<Name>.data-model.md` using the structure in
[`../../templates/data-model.md`](../../templates/data-model.md).

The file should make the seven CSDP steps inspectable in text form.
If the concept has no state, the file should still exist and say so
explicitly, with the later steps marked not applicable.

## What this file is not

- Not a storage mapping guide
- Not a DDL generator
- Not a place for RDF properties, SQL columns, or collection names
- Not a full ORM-ML serialization format