# Sync data-flow patterns — legal data joins

A sync's job is to take a completion event and invoke the next action. The
next action usually needs **arguments** the completion event did not
carry. The question this file answers is: *where can a sync legally get
those arguments from?*

The four data-flow patterns (**A/B/C/D**, defined in
[`SYNCHRONIZATIONS.md`](SYNCHRONIZATIONS.md) §"Where-clause patterns") group
into **two categories**, and only one crosses concept boundaries:

| Category | Description | Crosses concept boundary? |
|---|---|---|
| **Internal flow data** | Data from the trigger event, a sibling action's output, or a literal constant. All bound through the shared flow token — no other concept is read. | No |
| **Concept-state read** | A read against another concept's named persistence region (graph, table, collection). The only legal cross-concept data access. | Yes |

Patterns A (flow-token join), B (flow-sibling join), and C (sync constant) are
all *internal flow data* and are not flagged for coordination review. Only
concept-state reads (Pattern D) require explicit annotation and appear in the
Stage 03a coordination review.

---

## Internal flow data (no cross-concept read)

The sync gets its data from the same flow — either the trigger action's
input/output, a previous action's output, or a literal baked into the
sync itself. All of these ride the shared flow token and do not read
another concept's persistence:

```
when:  Web/request: [ method: "login" ; email: ?email ] => [ routed ]
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
    Web/request: [ method: "password_reset" ; identifier: ?username ]
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
visible in the sync spec and appears in the Stage 03a coordination review
as a concept-state read.

**This is the equivalent of `someOtherObject.getFoo()` in OO** — the
most tightly coupled thing one component can do to another. Unlike OO,
the coupling is **explicit and visible**: every concept-state read
appears as a row in the sync spec and again in the 03a per-concept
card's Section 2. It cannot happen invisibly.

## Joined rules: naming a conjunct

A joined (multi-`when`) rule matches several completions in one flow. Each
conjunct is named, and a binding names which one it reads:

```
when {
    list: Catalog/list: [ id: ?id ] => [ Listed ; id: ?id ]
    tag:  Tagging/tag:  [ id: ?id ] => [ Tagged ; id: ?id ]
}
where {
    bind ( list.id as ?listedId )   // Pattern B — list's completion field
    bind ( tag.param  as ?p )       // Pattern A — tag's invocation input
}
```

- `name.field` reads the named conjunct's **completion** field — still
  internal flow data (Pattern B), no cross-concept read.
- `name.param` reads the named conjunct's **invocation input** — still
  internal flow data (Pattern A).
- A `Concept: { ... }` state read inside a join is still a Pattern D
  concept-state read and is audited exactly as before.

Joining does not add a new data category; it only scopes an existing A/B
binding to one named conjunct.

## Collect / aggregate bindings

`collect`/`distinct`/`scan`/`collectBy` are **value-producing sources**, not
a query/filter surface:

```
where {
    collect by ?article ( Tagging: { ?article tags: ?tag } as ?tags )
}
```

- The inner source is itself an A/B/C/D binding (`Tagging: { … }` here is a
  Pattern D concept-state read, so the audit is unchanged).
- `collect` only gathers the values that source already yields into one
  `List`; `distinct` de-duplicates and orders; `collectBy` groups frames.
- No filters, no arithmetic, no JSON assembly. This is the deliberate
  distinction from conceptbox's imperative `frames.query/filter/collectAs`
  (`SYNCHRONIZATIONS.md` §"Collect", R3).

### Absence (negative state pattern)

`absent ( Concept ; ?subject ; predicate )` keeps a frame only if `?subject`
has **no** value for that predicate; the four-operand form narrows it to a
value. It is a concept-state read that binds nothing — a **D⁻** read — so it is
annotated and reviewed exactly like a positive one.

```
where {
    fanOut ( ?loanId ; "Lending" ; "borrower" ; ?memberId )   # the member's loans
    absent ( "Lending" ; ?loanId ; "returnedAt" )             # ... that are still open
    collect ( ?loanId as ?openLoans )
}
```

`absent` is not `filter`: it cannot compute, cannot assemble, and can only
negate a state pattern (R3). It fails **closed** — an unbound subject drops the
frame, so a rule never asserts an absence it could not check. A `where` that
ends with no frames does not fire; that is why an aggregate over a possibly
empty set must use `collectBy` (empty-safe), not `collect`.
See `maintenance/engine-absent-state-guard.md`.

---

## Compensation (post-commit undo)

CLAD has no transactions: a downstream action that fails completes with a named
`error` outcome, and the actions that already committed stay committed. The
paper's *earlier* transactional scheme (§3) suppressed a failed chain by aborting
its trigger; the paper's final scheme — and CLAD — drop that. Compensation is
therefore **an ordinary sync**: match the downstream failure outcome in the same
flow and call the owning concept's compensating action.

```
sync ReleaseReservationWhenPaymentFailed

when {
    pay:       Payment/charge:    [ order: ?order ] => [ error: ?err ]
    reserved:  Inventory/reserve: [ order: ?order ] => [ Reserved ; unit: ?unit ]
    requested: Web/request: [ route: "checkout" ] => [ Routed ]
}
then {
    Inventory/release: [ unit: ?unit ]
}
```

- The compensating action (`release`) belongs to the concept that owns the state
  (`Inventory`), never to the sync — R3.
- It is a normal rule: a joined `when` (the failure **and** the earlier success in
  one flow) plus a declarative `then`. The engine fires it after both completions
  are committed, so it sees exactly what happened.
- This is the deliberate replacement for transactional rollback — the paper's §3
  transaction elimination. The undo is a rule you can read, not an exception
  handler hidden in an engine.

---

## Why the distinction matters

### R1 stays enforceable

Without this distinction, a reviewer reading a sync sees "the sync
mentions another concept" and has no quick way to tell whether that
crossing is legal. The rule is: *if the data is internal to the flow,
no concept boundary was crossed. If the `where` clause names another
concept, the crossing is real and gets additional review.*

### Concept-state reads are visible at review time

Every concept-state read (Pattern D) appears as:
- A row in the sync's `where` clause
- A row in Section 2 of the concept's 03a coordination review card
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

The canonical fire-after-commit profile implements concept-state reads
through the `FactStore`/`Region` SPI: internal flow data is joined through
the shared flow id in the action log, and a concept-state read is a named
`StateRead` against another concept's `Region`. The legacy Jena profile
implements the same distinction against named graphs by IRI; the relational
profile against per-concept tables. Every backend honours the same rule:
internal flow data needs no review; a concept-state read is flagged in
Stage 03a.
