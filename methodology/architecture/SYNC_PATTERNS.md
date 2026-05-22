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

The sync reads from the **original request** that started the chain
(the root `Web.handle` flow token). Every action in the chain shares
the same flow-token id, so the original inputs are always reachable.

```
when:  <SomeConcept>.<action>(...) -> <Outcome>
where: payload = lookupRequest(flowToken).body
       email   = payload.email
then:  <NextConcept>.<action>(email)
```

- **Where:** the root `Web.handle` invocation for this flow.
- **Key:** the flow-token id (implicit; shared by every action in the
  chain).
- **Use when:** the data was submitted in the original HTTP request
  and has not been transformed since.

### Pattern B — Flow-sibling join

The sync reads from the **output of an earlier action in the same
chain** (a "sibling" — same flow token, completed earlier).

```
when:  PasswordAuth.verify(...) -> Ok
where: userId = result_of(User.lookupByUsername).userId
then:  Session.grant(userId)
```

- **Where:** an earlier action's completion record in the same flow.
- **Key:** the flow-token id (matches the prior action's record in
  the action log / engine state).
- **Use when:** the value was produced by a previous concept action
  in the same causal chain.

### Pattern C — Sync constant

The sync injects a **value baked into the rule itself** — not joined
from anywhere, just a literal. This is the point where the system's
generality (a concept that takes any role) collapses into a specific
flow (a registration sync that always passes `role = CONSUMER`).

```
when:  Web.handle(POST /register/consumer, body) -> Routed
where: role = "CONSUMER"     -- fixed by which sync this is
then:  User.register(body.username, role)
```

- **Where:** nowhere — the value is part of the sync's text.
- **Key:** none.
- **Use when:** the value is determined by *which sync this is*, not
  by runtime data. The concept stays general; the sync names the
  specific case.

### Pattern D — Concept-state join

The sync reads from **another concept's named region** (its named
graph / table / collection). This is the **only** pattern that
crosses a concept boundary at read time.

```
when:  Web.handle(POST /password/reset, body) -> Routed
where: user = lookup(concept = User, byUsername = body.username)
       email = user.email
then:  Mailer.send(email, resetLink(user.id))
```

- **Where:** another concept's named region.
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

## What goes in Stage 02b vs Stage 03

Stage 02b stays concrete: `# | When | Then | Inputs | Outcome | Why this
step`. It does **not** carry `Where` / `Key` columns. At that stage,
the table captures causal choreography only.

Stage 03 is the first place where join provenance is spelled out. The
sync's Contract Matrix and `where:` clause make the data source explicit
using pattern notation (`A: ...`, `B: ...`, `C: ...`, `D: ...`). That
keeps the derivation path reviewable:

- Stage 02b says exactly which `When -> Then` edge is approved.
- Stage 03 says where the downstream action's arguments come from.
- Stage 03a audits those joins per concept.

Stage 03 `where` clauses are binding-only. They may bind fields from a
flow token, prior action output, sync constant, or named concept graph.
They may not compute values, assemble JSON, or reshape payloads. If a
downstream action needs a new shape, the upstream concept action must
emit that shape explicitly.

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
