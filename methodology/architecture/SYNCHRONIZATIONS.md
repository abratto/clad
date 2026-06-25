# Synchronizations

A **synchronization** (sync) is a declarative coordination rule between
concepts. It says: *when this action on concept A completes with this
outcome, then run that action on concept B with these arguments.*

Syncs are the **only** place where two concepts come into contact. All
business-level wiring lives here.

## Shape

```
Sync: LoginGrantsSession
  when:  PasswordAuth.verify(userId, password) -> Ok
  where: C: session = "auto-generated"
  then:  Session.open(userId, session)
         Web.respond(token: session)
```

Three clauses:

| Clause | What it does |
|---|---|
| `when`  | Matches a completed action on a concept and pattern-matches its outcome |
| `where` | Binds locals — pure expressions, no side effects |
| `then`  | Invokes one or more actions on (other) concepts |

A sync **fires only on a completion**, never mid-action. It cannot
observe a concept's state directly. It cannot call back into the
concept whose action triggered it without going through that concept's
public actions.

## What a sync must not do

- **Branch on business conditions.** `if user.role == "admin"` does not
  belong in a sync. That decision is a concept's responsibility (e.g.
  an `Authorization` concept whose `permit` action returns an outcome
  the sync matches on).
- **Call back into the triggering concept's internals.** It can call
  another action on the same concept, but only as one would from the
  outside.
- **Persist its own state.** Syncs are stateless rules. Anything that
  needs memory belongs in a concept.
- **Touch I/O directly.** I/O happens in concepts (typically `Web`,
  `Mailer`, etc.). Syncs orchestrate those concepts.
- **Hide orchestration in an imperative coordinator class.** A class
  that sequences ordered domain calls with `if` / `then` branching is
  not a sync in CLAD terms, even if it sits in a `sync` package. In the
  Java profile, executable syncs are `SyncAgent` subclasses; a
  `*Coordinator` or `*Orchestrator` class is a design smell that should
  fail review unless it is a thin transport/runtime adapter with an
  explicit waiver.

## How a sync gets its data — the four patterns

Every `where` clause in a sync uses **exactly one** of four named
patterns: A (flow-token join), B (flow-sibling join), C (sync
constant), D (concept-state join). Pattern D is the only one that
crosses a concept boundary at read time, which is what makes hard
rule R1 enforceable by inspection of the sync spec.

The full pattern catalogue, with worked examples and anti-patterns,
is in [`SYNC_PATTERNS.md`](SYNC_PATTERNS.md). Stage 03 must consume
it; Stage 03a (per-concept dependency review) is built on it.

## Why this discipline

If syncs can branch and hold state, they become a hidden controller and
the system stops being legible — you can no longer read a concept and
know what it does, because some sync somewhere may overrule it. Keeping
syncs declarative is what preserves the WYSIWID property.

In implementation stages, treat imperative orchestration as a defect,
not as an alternative style. If a scenario can only be made green by a
coordinator that orders domain calls and chooses the final branch inline,
the sync set or concept outcomes are incomplete and the work must return
to Stage 03 or 04e-red.

## Composition

Multiple syncs may fire on the same trigger. They run independently and
in unspecified order; they must be commutative (their effects must not
depend on which fires first). If two syncs would conflict, the
conflict is a design error to be resolved by promoting the conflicting
logic into a concept.

## Authoring a sync (for agents)

When stage `03_syncs/` runs, the agent should produce one
`<name>.sync.md` per coordination rule identified by the use case and
the concept specs. Use [`templates/sync.md`](../../templates/sync.md).
Each sync must reference, in a `Cites` section, the use-case scenario
that demands it; this is what makes stage 5 verification possible.
