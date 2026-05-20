# Data model notes — drafting per-concept conceptual data models

CLAD's Stage 03b derives a **profile-neutral conceptual data model**
from each concept's approved `state` section and any approved Pattern D
exposure from dependency review. This file is the procedural reference
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
- consistency with approved Pattern D exposure from 03a
- avoidable redundancy
- completeness of the conceptual model for this concept

## Cross-concept rule

Do not model foreign keys or direct region-sharing across concepts. If a
concept carries another concept's identifier, it is an opaque value
whose runtime meaning is established by syncs, not by a schema-level
relationship.

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