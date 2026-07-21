# Sync data-flow patterns — legal data joins

A sync's job is to take a completion event and invoke the next action. The
next action usually needs **arguments** the completion event did not
carry. The question this file answers is: *where can a sync legally get
those arguments from?*

There are exactly **two** categories, and only one crosses concept
boundaries:

| Category | Description | Crosses concept boundary? |
|---|---|---|
| **Internal flow data** | Data from the trigger event, a sibling action's output, or a literal constant. All bound through the shared flow token — no other concept is read. | No |
| **Concept-state read** | A read against another concept's named persistence region (graph, table, collection). The only legal cross-concept data access. | Yes |

This replaces the earlier A/B/C/D labelling. Patterns A (flow-token join),
B (flow-sibling join), and C (sync constant) are all *internal flow data*
and are not flagged for dependency review. Only concept-state reads
(formerly Pattern D) require explicit annotation and appear in the
Stage 03a dependency review.

---

## Internal flow data (no cross-concept read)

The sync gets its data from the same flow — either the trigger action's
input/output, a previous action's output, or a literal baked into the
sync itself. All of these ride the shared flow token and do not read
another concept's persistence:

```
when:  Web/handle: [ method: "login" ; email: ?email ] => [ routed ]
then:  PasswordAuth/check: [ password: ?password ]  ← from trigger input

when:  User/lookupByUsername: [ username: ?u ] => [ userId: ?id ]
then:  Session/grant: [ userId: ?id ]               ← from sibling output

when:  Session/grant: [ userId: ?id ] => [ sessionToken: ?token ]
then:  Web/respond: [ status: 200 ; sessionToken: ?token ]  ← literal 200
```

All three are legal without special review. The data lives within the
flow chain and no concept boundary is crossed.

## Concept-state read (crosses concept boundary)

The `where` clause reads from **another concept's named persistence
region** (its named graph / table / collection). This is the **only**
legal way to read another concept's state — and it must be explicitly
visible in the sync spec:

```
sync PasswordResetNotification

when {
    Web/handle: [ method: "password_reset" ; identifier: ?username ]
      => [ routed ]
}
where {
    User: { ?user email: ?email . name: ?username }
}
then {
    Mailer/send: [ to: ?email ; body: "Your reset link: ..." ]
}
```

The `User: { ... }` block reads the `User` concept's named region at
runtime, joined on `?username` from the trigger. This is explicitly
visible in the sync spec and appears in the Stage 03a dependency review
as a concept-state read.

**This is the equivalent of `someOtherObject.getFoo()` in OO** — the
most tightly coupled thing one component can do to another. Unlike OO,
the coupling is **explicit and visible**: every concept-state read
appears as a row in the sync spec and again in the 03a per-concept
card's Section 2. It cannot happen invisibly.

---

## Why the distinction matters

### R1 stays enforceable

Without this distinction, a reviewer reading a sync sees "the sync
mentions another concept" and has no quick way to tell whether that
crossing is legal. The rule is: *if the data is internal to the flow,
no concept boundary was crossed. If the `where` clause names another
concept, the crossing is real and gets additional review.*

### Concept-state reads are visible at review time

Every concept-state read (formerly Pattern D) appears as:
- A row in the sync's `where` clause
- A row in Section 2 of the concept's 03a dependency review card
- A row in `pattern-d-summary.md` for the feature
- A field in the concept's 03b data model

### Cross-flow consistency

If the same downstream action is invoked via internal flow data in some
flows and a concept-state read in others, that is almost always a bug —
the data source disagrees between flows. Stage 03a surfaces this by
listing each action's invocations across all flows and flagging where the
source differs.

---

## Anti-patterns

- **Concept-state read used for data the trigger already carries.** If
  the needed value is in the trigger or a sibling's output, use internal
  flow data. A concept-state read is the most expensive option (a real
  cross-concept read) and should not be the default.
- **Hidden concept-state read.** Computing a derived value inside the sync
  using *another concept's* state, but not naming that concept in the
  `where` clause. The concept must be named explicitly so 03a can list it.
- **Literal treated as variable.** If a "constant" is actually a function
  of the request, it is internal flow data — write it that way in `when`.

---

## Profile note

The Java/Micronaut/Jena reference profile implements concept-state reads
against a concept's named graph by IRI. Internal flow data is joined
through the shared flow token in the action log. Other profiles
(relational, document, in-memory) implement the same distinction against
their respective storage layers.
