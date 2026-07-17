# Synchronizations

A **synchronization** (sync) is a declarative coordination rule between
concepts. It says: *when this action on concept A completes with this
outcome, then run that action on concept B with these arguments.*

Syncs are the **only** place where two concepts come into contact. All
business-level wiring lives here.

## Shape

```
sync WhenPasswordAuthCheckOkThenSessionGrantForLogin

when {
    PasswordAuth/check: [ userId: ?user ; password: ?pass ] => [ ok ]
}
then {
    Session/grant: [ userId: ?user ]
}
```

Three clauses, written as `{ }` blocks:

| Clause | What it does |
|---|---|
| `when`  | Matches one or more completed actions and their outcomes. All matched actions must share the same flow token. |
| `where` | Declared state queries, identifier minting, and variable bindings (see Expressiveness below). May be omitted when no bindings are needed. |
| `then`  | Invokes one or more actions on (other) concepts with arguments derived from when/where bindings. |

A sync **fires only on a completion**, never mid-action. It cannot
observe a concept's state directly (except via the `where` clause's
explicit `Concept: { ... }` syntax — that is Pattern D and appears in
the 03a dependency review audit). It cannot call back into the concept
whose action triggered it without going through that concept's public
actions.

### Syntax elements

| Element | Meaning | Example |
|---|---|---|
| `sync <Name>` | Declares a sync rule | `sync WhenPasswordAuthCheckOkThenSessionGrantForLogin` |
| `Concept/action:` | Qualifies an action within its concept (slash separator, colon after) | `PasswordAuth/check:` |
| `[ param: value ; ... ]` | Named argument brackets, semicolon-separated | `[ userId: ?user ; password: ?pass ]` |
| `=> [ output: ?var ]` | Matches an action's completion output | `=> [ ok ]` or `=> [ userId: ?u ]` |
| `?variable` | Binding scoped across the entire sync | `?user`, `?pass` |
| `{ }` | Block delimiters for when/where/then | `when { ... }` |

## Naming

A sync name must read as a compressed `when X then Y` rule:

```
When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]
```

Rules:

- Prefix every sync name with `When`.
- Use `Then` as the separator between the trigger side and target side.
- Use PascalCase for the Stage 03 sync name and `.sync.md` file stem.
- Derive `TriggerConcept`, `TriggerAction`, `TargetConcept`, and
  `TargetAction` directly from the first `when` and `then` signatures.
- Derive `TriggerCompletion` from the first completion token in the
  `when` arrow's right side. For `[ ok ; userId: ?u ]`, use `Ok`; for
  `[ error: "notFound" ]`, use `NotFound`; for `[ refused ]`, use
  `Refused`.
- Omit `TriggerCompletion` only when the trigger has no completion token.
- Append `For<Scope>` when the same trigger/target edge can occur in
  multiple routes, flows, use cases, or other scopes.
- The `sync <Name>` header and filename stem must match exactly. Profile
  implementations should lower the same stem mechanically; for Java, the
  class name is the same PascalCase stem and `syncName()` is lower camel case.

Example:

```
sync WhenPasswordAuthCheckOkThenSessionGrantForLogin

when {
    PasswordAuth/check: [ userId: ?user ; password: ?pass ] => [ ok ; userId: ?user ]
}
then {
    Session/grant: [ userId: ?user ]
}
```

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

CLAD recognises **exactly four** data-flow patterns for matching how
a `then` clause's arguments are bound:

| Pattern | Source | What it looks like |
|---|---|---|
| **A** (flow-token join) | A `?variable` declared in the `when` clause's input or output | `?pass` bound from `Web/handle: [ password: ?pass ]` |
| **B** (flow-sibling join) | A `?variable` carried by an earlier action's completion in the same flow | `?user` from `User/lookupByUsername: [...] => [ userId: ?user ]` |
| **C** (sync constant) | A literal value baked into the sync rule itself | `status: 200` in a `Web/respond` call |
| **D** (concept-state join) | A `Concept: { ... }` block inside the `where` clause that reads concept state | `User: { ?user email: ?email }` |

Pattern D is the only one that crosses a concept boundary at read time,
which is what makes hard rule R1 enforceable by inspection of the sync
spec. Patterns A and B both work through the shared flow token — the
sync sees these bindings without any cross-concept read.

The full pattern catalogue, with worked examples, anti-patterns, and
03a audit guidance, is in [`SYNC_PATTERNS.md`](SYNC_PATTERNS.md).
In the sync's source file, patterns are documented in a "Where clause
patterns" table (see the [`templates/sync.md`](../../templates/sync.md)).
Stage 03a's dependency review scans this table for Pattern D rows.

## Where clause expressiveness

The paper's `where` clause is a **declarative query language** that
CLAD adopts in full. Within the `where { }` block, a sync may use:

### Identifier minting

```
bind ( uuid() as ?user )
```

Generates a fresh, unique identifier. Used to mint IDs for new entities
(e.g. creating a user, a session, an article). Only mechanical generation
is allowed — `uuid()` is a CLAD built-in; custom computation belongs in
concept actions.

### State queries across concepts

```
User: { ?user name: ?username ; email: ?email }
Profile: { ?profile bio: ?bio ; image: ?image }
```

Reads fields from named concept regions. This is Pattern D — every such
read is recorded in the Stage 03a dependency review. The syntax mirrors
SPARQL property patterns: a subject variable, a semicolon-separated list
of property bindings, and a dot (`.`) to terminate.

### Conditional reads

```
OPTIONAL { Tag: { ?article tag: ?tag } }
```

Reads a value if it exists; if the concept has no data for the given
identifier, the variable is left unbound rather than failing the sync.
This is the declarative way to express "include this field if present."

### Aggregation

```
BIND ( ?article AS ?_eachthen )
```

Groups bindings by the given key, so the `then` clause fires once per
unique key value rather than once per binding row. This is the
declarative equivalent of SPARQL's `GROUP BY`. Without `?_eachthen`, a
sync whose `where` produces multiple bindings (e.g. one per tag) would
fire the `then` clause once for each binding, which would produce a
response per tag instead of one response per article.

### What still does NOT belong in `where`

- **Business branching.** `if ?role = "admin"` belongs in a concept
  action's outcomes, not in `where`.
- **Side effects or I/O.** Reads are for binding; writes belong in
  `then` or in concept actions.
- **State mutation.** `where` is read-only.
- **Custom computation.** Hashing, signing, arithmetic, JSON assembly
  — all belong in concept actions. The `where` clause binds values;
  it does not compute them.

These constraints are what preserve the "syncs are declarative"
property (R3), even with the richer where-clause syntax.

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

## Relationship to the Meng & Jackson paper

CLAD's sync language is aligned with the paper's Section 5 syntax with
two intentional divergences:

| Area | Paper | CLAD |
|---|---|---|
| Web action name | `Web/request` | `Web/handle` — CLAD's bootstrap concept calls its entry action `handle`, not `request` (see [`WEB_CONCEPT.md`](WEB_CONCEPT.md)) |
| Outcome matching | `Concept/action: [ input ] => []` (empty brackets for no-output outcomes) | `Concept/action: [ input ] => [ outcomeName ]` (inlines the outcome name in the arrow's right side) |

Otherwise, the `when { }` / `where { }` / `then { }` block structure,
`Concept/action:` namespace qualifiers, `?variable` bindings, `bind()`
and `OPTIONAL` constructs, and `?_eachthen` aggregation all follow the
paper's design.

## Authoring a sync (for agents)

When stage `03_syncs/` runs, the agent should produce one
`<name>.sync.md` per coordination rule identified by the use case and
the concept specs. Use [`templates/sync.md`](../../templates/sync.md).
Each sync must reference, in a `Cites` section, the use-case scenario
that demands it; this is what makes stage 5 verification possible.
