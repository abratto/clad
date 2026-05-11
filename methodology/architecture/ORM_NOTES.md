# ORM notes — drafting per-concept state schemas

CLAD's stage 04a draws state schemas from each concept's `state`
section. This file is the procedural reference for that drafting:
*how* to turn a prose `state` section into a schema that respects
hard rule R2 (one named region per concept) and stays implementable
under whatever profile is in use (relational, RDF, document, in-mem).

The procedure is adapted from Mustafa Jarrar's **Object Role Modelling
(ORM/ORM-ML) Conceptual Schema Design Procedure** (CSDP). The
six-step CSDP is the canonical answer to "given a domain
description, how do I derive a normalised schema without skipping
steps?". CLAD borrows the *shape* of the procedure; it does not adopt
the full ORM-ML notation. See
[`../reference/CITATIONS.md`](../reference/CITATIONS.md) for the
primary source.

---

## When this file applies

Stage 04a only. If the profile is in-memory (no persistent store),
04a writes `_NOT_APPLICABLE.md` and this file does not apply.

## The six steps (CLAD adaptation of Jarrar CSDP)

For each concept independently — never look across concepts during
04a.

1. **Sample the state in concrete sentences.** From the concept's
   `state` section, write 3–5 example sentences in English that the
   schema must be able to express. *"User `u1` has username
   `alice`."* This grounds the next steps.
2. **Name the entity types and value types.** Mark each noun in your
   sample sentences as either an *entity* (has identity, e.g. `User`,
   `Session`) or a *value* (no identity, e.g. `username`, `createdAt`).
3. **Draw the fact types.** Each sample sentence becomes a fact type:
   `User has Username`, `Session belongsTo User`, etc. Keep them
   binary where possible.
4. **Apply uniqueness constraints.** Mark which fact roles are
   uniquely identifying. `Username uniquely identifies User`.
5. **Apply mandatory-role and other constraints.** Note nullability,
   value ranges, and any frequency constraints that arose from the
   concept's invariants.
6. **Check derivability.** If a fact can be derived from others, mark
   it derived rather than stored. Derived facts do not become columns.

The output of steps 1–6 is what gets written to the body of
`output/<Name>.orm.md` as the profile-neutral conceptual model.

## Post-walk: profile mapping note

After completing the six conceptual steps, record how the named region
for this concept is wired in the chosen profile. This note goes in
`## CSDP Notes` of the `.orm.md` file — **not** in the `## CSDP Walk`
section. The walk contains only steps 1–6.

The profile mapping note should state:
- The named region identifier (e.g. `<urn:clad:account>` for Jena)
- How each fact type maps to the profile's storage primitive
  (RDF property, column, document field)
- How uniqueness and mandatory constraints are expressed in the profile

See `## Profile mapping guidance` below for per-profile details.

## Profile mapping guidance

The conceptual model (steps 1–6) is always profile-neutral. The post-walk
profile mapping note records *where* the named region lives; the translation
varies by profile:

### RDF / Jena TDB2
- Each fact type → an RDF property in the concept's namespace
  (e.g. `account:hasEmail`, `account:hasPasswordHash`)
- Uniqueness constraint → `owl:InverseFunctionalProperty` on the
  property, or a SHACL `sh:PropertyShape` with `sh:maxCount 1` on
  the inverse
- Mandatory role → SHACL `sh:minCount 1`
- Enum value type → `owl:oneOf` restriction or SHACL `sh:in`
- The named region itself → one named graph URI per concept
  (e.g. `<urn:clad:account>`)

Do **not** write a `Field / Type / Constraints` table for an RDF
profile. That is a relational schema. RDF has no columns.

### Relational (PostgreSQL, SQLite, etc.)
- Each fact type → a column
- Uniqueness constraint → `UNIQUE` constraint
- Mandatory role → `NOT NULL`
- Enum → `CHECK` constraint or a lookup table
- Named region → one schema or table prefix per concept

### Document (MongoDB, etc.)
- Each fact type → a document field
- Constraints → JSON Schema or validator annotations
- Named region → one collection per concept

## Cross-concept rule (R1, R2)

You will be tempted, between two concepts, to model a foreign key
("Session.userId references User.id"). **Do not.** A `userId` in
`Session`'s state is just an opaque identifier whose meaning is
established by a sync at runtime, not by a database constraint. If
you draw an FK across concepts in 04a, you have introduced a hidden
import and broken R1.

If two concepts genuinely need to coordinate over an identifier, the
fact lives in the responsibility map and the linkage runs through a
sync — never through a schema-level relationship.

## Common shortcuts (and when they bite)

- **Skipping step 1** ("the state section is short, just write the
  schema"). The sample sentences are what catch missing constraints.
  Skip them and step 5 has nothing to anchor to.
- **Modelling enums as separate entities.** Outcomes
  (`Ok`/`BadPassword`/...) are not entities; they are values
  enumerated by the spec. Keep them as values.
- **Optimising the schema for queries.** 04a is a *conceptual*
  schema, not a physical one. Indexes, denormalisation, and sharding
  belong to the profile's implementation, not to 04a's output.

## What this file is **not**

- Not a tutorial in ORM-ML notation. If you want the notation, read
  Jarrar's papers directly (cited in `CITATIONS.md`).
- Not a generator for SQL DDL. The output is markdown describing fact
  types; the profile turns that into DDL or RDF triples.
- Not a substitute for the per-profile reference docs (e.g.
  `reference-impl/java-micronaut-jena/README.md`), which describe how
  the profile's named regions are wired.

---

## Working method — chat-first, per-step confirmation

Stage 04a runs **interactively**, not as a single batch:

1. Walk the six steps **one at a time** in chat. After each step,
   surface what was decided and end with the standard gate question:
   *"Do you agree with this step? Any corrections before I continue?"*
2. Wait for human confirmation before moving to the next step. Do
   not pre-emptively draft step 4 while presenting step 3.
3. Commit `output/<Name>.orm.md` (and any profile artefacts like
   `ORM.xml`) **only after all six steps and the post-walk profile
   mapping note are confirmed**. Half-walked drafts do not get
   committed.

This is slower per concept than batching, and that is the point —
ORM mistakes that escape Stage 04a propagate into 04b SPECs, into
test fixtures, and into migrations. Catching a wrong constraint at
step 5 is cheap; catching it at 04d is not.

### Empty-model shortcut

If **step 1** (sample sentences) shows that the concept has no
state — its `state` section is empty and no spec WHERE clause
references it — skip steps 2–6. Confirm once with the human:

> *"`<Concept>` has no persistent state. I'll write
> `output/<Concept>.orm.md` recording that fact and skip steps 2–6.
> Do you agree?"*

On confirmation, the file records *"No state — CSDP steps 2–6 do not
apply"* and the stage advances. No further interaction needed for
that concept.

## Output format — `## CSDP Notes` section

Every committed `<Name>.orm.md` ends with a section titled
**`## CSDP Notes`**. This section is **not a transcript** of all
six steps — that would just duplicate the body of the file. It
records **only non-self-evident decisions**:

- Mid-walk corrections (e.g. *"Step 4 originally marked `email`
  uniquely identifying; revised after step 5 noted invariant
  permits two soft-deleted users to share an email."*).
- Conditional mandatory rationale (a role that is mandatory only
  under some condition, with the condition stated).
- Upstream artefact impacts (any change required to the concept
  spec, the responsibility map, or a sync as a result of this walk).

Format: one sub-section per noted decision, identified by step
number:

```
## CSDP Notes

### Step 3 correction — `expiresAt` is conditional, not unconditional
The first draft modelled `expiresAt` as an unconditional fact of
`Session`. Step 5 surfaced that anonymous sessions have no
expiry. Reverted to: `Session has expiresAt` mandatory iff
`Session.kind = "user"`.

### Profile mapping — exposing `email` to other concepts
Pattern D summary requires `User.email` to be readable by
`PasswordReset`. Added `email` to the `User` named region with
public visibility. Concept spec already exposed it as a state
field; no spec change needed.
```

If the walk had no notable decisions, write
*"No notable decisions — straight CSDP walk."* The section is
mandatory; its emptiness is itself a useful signal at review time.
