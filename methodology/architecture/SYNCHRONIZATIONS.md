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
  where: session = freshSessionId()
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

## Why this discipline

If syncs can branch and hold state, they become a hidden controller and
the system stops being legible — you can no longer read a concept and
know what it does, because some sync somewhere may overrule it. Keeping
syncs declarative is what preserves the WYSIWID property.

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
