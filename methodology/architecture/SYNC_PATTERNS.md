# Sync data-flow patterns — the four legal joins

A sync's job is to take a completion event and invoke the next action.
The next action usually needs **arguments** the completion event did
not carry. The question this file answers is: *where can a sync
legally get those arguments from?*

CLAD recognises **exactly four** patterns. Naming them up front —
A, B, C, D — turns "how does this sync get its data?" from a design
puzzle into a label, and makes hard rule R1 enforceable by
inspection: only one of the four patterns crosses concept boundaries,
and that crossing is visible in the sync spec.

This file is a Layer-3 reference. It is consumed by Stage 03 (sync
authoring) and Stage 03a (per-concept dependency review). Adapted
from prior work documented in `methodology/reference/CITATIONS.md`.

---

## The four patterns

### Pattern A — Flow-token join

The `then` clause uses a `?variable` that was declared in the `when`
clause's action pattern. The variable binds through the shared flow
token — every action in the chain can see it without a cross-concept
read.

```
when:  Web/handle: [ method: "register" ; email: ?email ] => [ routed ]
then:  User/register: [ email: ?email ]
```

The `?email` variable was bound by the trigger event (the `Web/handle`
completion). It flows into `then` through the shared flow token.

- **Source:** the trigger token's input or output fields.
- **Key:** the flow-token id (implicit; shared by every action in the
  chain).
- **Use when:** the data was submitted in the original HTTP request
  and has not been transformed since.

### Pattern B — Flow-sibling join

The sync reads a `?variable` that was **emitted by an earlier action
in the same chain** (a "sibling" — same flow token, completed earlier).
In paper sync syntax, this looks the same as Pattern A: a `?variable`
declared in the `when` clause's output that flows into `then`. The
distinction is that the binding originated from a sibling action's
completion, not from the root trigger.

```
when: {
    User/lookupByUsername: [ username: ?u ] => [ userId: ?id ]
}
then: {
    Session/grant: [ userId: ?id ]
}
```

`?id` was emitted by `User/lookupByUsername`'s completion (a sibling
action in the same flow). It is not a field from the original request.

- **Source:** an earlier action's completion record in the same flow.
- **Key:** the flow-token id (matches the prior action's record in
  the action log / engine state).
- **Use when:** the value was produced by a previous concept action
  in the same causal chain.

### Pattern C — Sync constant

The `then` clause uses a **literal value baked into the rule itself**
— not joined from anywhere. This is the point where the system's
generality (a concept that takes any role) collapses into a specific
flow (a response sync that always passes status 200).

```
when: {
    Session/grant: [ userId: ?id ] => [ sessionId: ?sid ]
}
then: {
    Web/respond: [ status: 200 ; body: { sessionToken: ?sid } ]
}
```

The literal `200` is determined by *which sync this is*, not by runtime
data. `?sid` is Pattern B (flow-sibling join) — the status code literal
is Pattern C.

- **Source:** nowhere — the value is part of the sync's text.
- **Key:** none.
- **Use when:** the value is determined by *which sync this is*, not
  by runtime data. The concept stays general; the sync names the
  specific case.

### Pattern D — Concept-state join

The `where` clause reads from **another concept's named region** (its
named graph / table / collection). This is the **only** pattern that
crosses a concept boundary at read time. In paper sync syntax, this
appears as a `Concept: { ... }` block inside `where { }`.

```
sync PasswordResetNotification

when {
    Web/handle: [ method: "password_reset" ; identifier: ?username ] => [ routed ]
}
where {
    User: { ?user email: ?email .
            name: ?username }
}
then {
    Mailer/send: [ to: ?email ; body: "Your reset link: ..." ]
}
```

The `User: { ... }` block reads the `User` concept's named region at
runtime, joined on `?username` (which was bound by the `when` clause).
This is explicitly visible in the sync spec and appears in the Stage 03a
dependency review as a Pattern D read.

- **Source:** another concept's named region.
- **Key:** an identifier that the trigger output carried (or that
  Pattern A made available from the request).
- **Use when:** the value lives in a different concept's persistent
  state and no earlier action in the chain returned it.

---

## Why naming them matters

### R1 stays enforceable

Without these names, a reviewer reading a sync sees "the sync
mentions another concept" and has no quick way to tell whether that
crossing is legal. With the names, the question is reduced to: *which
pattern is this?* If the answer is A, B, or C, no concept-boundary
crossing happened. If the answer is D, the crossing is real and gets
the additional review treatment described below.

### Pattern D is field access on another object

In OO terms (see [`MENTAL_MODEL.md`](MENTAL_MODEL.md)), Pattern D is
the equivalent of `someOtherObject.getFoo()` — the most tightly
coupled thing one component can do to another. Unlike OO, the
coupling is **explicit and visible**: every Pattern D appears as a
row in the sync spec and again in the
[03a dependency review](../implementation/STAGES.md). It cannot
happen invisibly.

### Cross-flow inconsistency becomes a mechanical check

If the same downstream action is invoked via **different patterns in
different flows**, that is almost always a bug — the data source
disagrees between flows, and the ORM model will end up with
contradictory constraints. Stage 03a surfaces this by listing each
action's invocations across all flows and flagging where the pattern
differs.

---

## Pattern labels as audit annotations

Pattern labels (A/B/C/D) are no longer the primary surface syntax inside
sync specs. The sync's `when { }` / `where { }` / `then { }` blocks use
paper syntax directly (see [`SYNCHRONIZATIONS.md`](SYNCHRONIZATIONS.md)).
The labels survive as **audit annotations** — each sync's "Where clause
patterns" table (see [`templates/sync.md`](../../templates/sync.md))
maps every binding to its pattern for Stage 03a's dependency review.

| Stage | Uses patterns for |
|---|---|
| 03 (sync authoring) | Label each binding in the Where clause patterns table |
| 03a (dependency review) | Scan for Pattern D (concept-state join) rows; flag cross-concept reads |
| 05 (verification) | Cross-check that every observed data flow has an authorised pattern |

## What goes in Stage 02b vs Stage 03

Stage 02b stays concrete: `# | When | Then | Inputs | Outcome | Why this
step`. It does **not** carry `Where` / `Key` columns. At that stage,
the table captures causal choreography only.

Stage 03 is the first place where join provenance is spelled out. The
sync's Contract Matrix and rule clause (`when { }` / `where { } / `then { }`)
make the data source explicit. The Where clause patterns table maps each
binding to its pattern (A/B/C/D). This keeps the derivation path reviewable:

- Stage 02b says exactly which `When -> Then` edge is approved.
- Stage 03 says where the downstream action's arguments come from.
- Stage 03a audits those joins per concept.

Stage 03 `where` clauses may use `bind()`, `OPTIONAL`, and state queries
as described in [`SYNCHRONIZATIONS.md`](SYNCHRONIZATIONS.md). They may
**not** branch on business conditions, perform I/O, mutate state, or
execute custom computation. If a downstream action needs a new shape,
the upstream concept action must emit that shape explicitly.

Worked examples live in
[`../../templates/sync.md`](../../templates/sync.md)
and the UC-00-login sync pack under
[`../../features/UC-00-login/stages/03_syncs/`](../../features/UC-00-login/stages/03_syncs/).

---

## Anti-patterns

- **"Pattern E — call the other concept's action."** That is just a
  sync, and the call belongs in `then`, not `where`. The four
  patterns are about *reading data*, not invoking actions.
- **Pattern D used for data the trigger already carries.** If the
  needed value is in a flow-sibling's output, use Pattern B. Pattern
  D is the most expensive option (a real cross-concept read) and
  should not be the default.
- **Hidden Pattern D.** Computing a derived value inside the sync
  using *another concept's* state, but not mentioning that concept in
  `where`. The concept must be named explicitly so 03a can list it.
- **Pattern C with a value that varies per request.** If the constant
  is actually a function of the request, it is Pattern A — write it
  that way.

---

## Profile note

The Java/Micronaut/Jena reference profile implements these patterns
on top of the action log under
`reference-impl/java-micronaut-jena/`. Pattern B reads sibling
completions from the actions graph; Pattern D reads the target
concept's named graph by IRI. Other profiles (relational, document,
in-memory) implement the same four reads against their respective
storage layers.
