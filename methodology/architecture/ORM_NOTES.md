# ORM notes — drafting per-concept state schemas

CLAD's stage 04a draws state schemas from each concept's `state`
section. This file is the procedural reference for that drafting:
*how* to turn a prose `state` section into a schema that respects
hard rule R2 (one named region per concept) and stays implementable
under whatever profile is in use (relational, RDF, document, in-mem).

The procedure is adapted from Mustafa Jarrar's **Object Role Modelling
(ORM/ORM-ML) Conceptual Schema Design Procedure** (CSDP). The
seven-step CSDP is the canonical answer to "given a domain
description, how do I derive a normalised schema without skipping
steps?". CLAD borrows the *shape* of the procedure; it does not adopt
the full ORM-ML notation. See
[`../reference/CITATIONS.md`](../reference/CITATIONS.md) for the
primary source.

---

## When this file applies

Stage 04a only. If the profile is in-memory (no persistent store),
04a writes `_NOT_APPLICABLE.md` and this file does not apply.

## The seven steps (CLAD adaptation of Jarrar CSDP)

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
7. **Map to the profile.** Translate the resulting fact types into
   the profile's storage shape — one **named region** per concept
   (R2). For Java/Jena that is one named graph; for a relational
   profile it would be one schema or table prefix.

The output of step 7 is what gets written to `output/<Name>.orm.md`.

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
