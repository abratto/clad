# Synchronizations

A **synchronization** (sync) is a declarative coordination rule between
concepts. It says: *when this action on concept A completes with this
outcome, then run that action on concept B with these arguments.*

Syncs are the **only** place where two concepts come into contact. All
business-level wiring lives here.

Formally, a sync is a function over a causal flow that maps completed
actions into **frames** (sets of variable bindings). Three phases,
all declarative:

1. **`when`** — a multi-action join selecting which completed actions
   in the flow match specified patterns (realized directly by named
   conjuncts; see §"Joins (multi-`when`)").
2. **`where`** — a purely read-only query and filter phase. Frames are
   refined and expanded (fan-out) by querying concept state, but **no
   state mutation occurs here** — the `where` clause is a declarative
   binding phase, not imperative code (R3).
3. **`then`** — action emission. Each surviving frame produces one or
   more invocations (one per frame).

This model ensures three guarantees: syncs never mutate state during
inspection, execution is deterministic per frame set, and all matching
is scoped to a single causal flow token.

## Shape

```
sync GrantWhenCheckOk

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
explicit `Concept: { ... }` syntax — a concept-state read — appears in
the 03a coordination review audit). It cannot call back into the concept
whose action triggered it without going through that concept's public
actions.

### Syntax elements

| Element | Meaning | Example |
|---|---|---|
| `sync <Name>` | Declares a sync rule | `sync GrantWhenCheckOk` |
| `Concept/action:` | Qualifies an action within its concept (slash separator, colon after) | `PasswordAuth/check:` |
| `[ param: value ; ... ]` | Named argument brackets, semicolon-separated | `[ userId: ?user ; password: ?pass ]` |
| `=> [ output: ?var ]` | Matches an action's completion output | `=> [ ok ]` or `=> [ userId: ?u ]` |
| `?variable` | Binding scoped across the entire sync | `?user`, `?pass` |
| `{ }` | Block delimiters for when/where/then | `when { ... }` |

## Naming

A sync name reads action-first (grammar v3, see
`maintenance/sync-name-grammar-v3.md`; the v2 `For<Scope>` form and the
pre-v0.6 condition-first form survive only in historical maintenance records):

```
<TargetAction>When<TriggerAction><TriggerCompletion>
```

Rules:

- Lead with the **effect** — the `then` side — because that is what a
  reader of a sync pack or a `causedBySync` back-trace wants first.
- Use `When` as the separator between the effect and its trigger.
- Use PascalCase for the Stage 03 sync name and `.sync.md` file stem.
- Name by **action**, not by concept. A sync is coordination, not a
  concept's property — it can involve several concepts — so the concept
  tokens are dropped by default. `Cataloguing.record` and `Stocking.record`
  both contribute `Record`.
- Derive `TargetAction` from the first `then` signature;
  `TriggerAction` from the first `when`.
- Derive `TriggerCompletion` from the first completion token on the right
  side of the `when` arrow, by its **base** token only: for
  `[ ok ; userId: ?u ]`, use `Ok`; for `[ error: "notFound" ]`, use
  `NotFound`; for `[ refused ]`, use `Refused`. Carried fields are
  body-visible and never join the name (`Routed`, not `RoutedRefName`).
- **Collision escalation.** When two different edges in one pack would share
  a name, the generator adds concept tokens back, in this order, and the
  parity check accepts every level:

  | Level | Form |
  |---|---|
  | 0 | `<TargetAction>When<TriggerAction><Completion>` |
  | 1 | `<TargetConcept><TargetAction>When<TriggerAction><Completion>` |
  | 2 | `<TargetAction>When<TriggerConcept><TriggerAction><Completion>` |
  | 3 | `<TargetConcept><TargetAction>When<TriggerConcept><TriggerAction><Completion>` |

  A payload variant of level 3 (`…<Completion><Payload>`) is the last
  resort for two outcomes of one action that differ only in payload.
- The `sync <Name>` header and filename stem must match exactly. Profile
  implementations lower the same stem mechanically; for Java, the class
  name is the same PascalCase stem (and per-rule carrier class if the
  profile authors one class per rule).

Example:

```
sync GrantWhenCheckOk

when {
    PasswordAuth/check: [ userId: ?user ; password: ?pass ] => [ ok ; userId: ?user ]
}
then {
    Session/grant: [ userId: ?user ]
}
```

For a **joined** (multi-`when`) rule the trigger side concatenates every
conjunct in declared order, separated by `And` after the `WhenJoin` marker:

```
<TargetAction>WhenJoin<A1><Out1>And<A2><Out2>…
```

```
sync RespondWhenJoinListListedAndTagTagged

when {
    a: Catalog/list: [ id: ?id ] => [ Listed ; id: ?id ]
    b: Tagging/tag: [ id: ?id ] => [ Tagged ; id: ?id ]
}
then {
    Web/respond: [ id: ?id ]
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
  Java profiles, executable syncs are declarative `SyncRule`s; a
  `*Coordinator` or `*Orchestrator` class is a design smell that should
  fail review unless it is a thin transport/runtime adapter with an
  explicit waiver.
- **Shape the transport response.** A `then` passes the **authored
  result** — the flat domain fields the exit action consumes. Response
  framing (a `body`/envelope wrapper, and in general the serialization
  step) is the **primary adapter's** job
  (see [`../overlays/PORTS_AND_ADAPTERS.md`](../overlays/PORTS_AND_ADAPTERS.md):
  the adapter "serialize[s] it to the transport's response"). So

  ```
  Web/respond: [ status: 200 ; sessionToken: ?sid ]      -- authored result
  Web/respond: [ status: 200 ; body: { sessionToken: ?sid } ]  -- framing: WRONG
  ```

  `status` is retained in `then` by convention (it is the exit action's
  response classification, and every chain table and respond spec carries it);
  the outcome→status mapping is the adapter's concern.
  Mechanised by `quality-gate/verify_sync_then_shape.py`.

## How a sync gets its data — the four patterns

CLAD recognises **exactly four** data-flow patterns for matching how
a `then` clause's arguments are bound:

| Pattern | Source | What it looks like |
|---|---|---|
| **A** (flow-token join) | A `?variable` declared in the `when` clause's input or output | `?pass` bound from `Web/request: [ password: ?pass ]` |
| **B** (flow-sibling join) | A `?variable` carried by an earlier action's completion in the same flow | `?user` from `User/lookupByUsername: [...] => [ userId: ?user ]` |
| **C** (sync constant) | A literal value baked into the sync rule itself | `status: 200` in a `Web/respond` call |
| **D** (concept-state join) | A `Concept: { ... }` block inside the `where` clause that reads concept state | `User: { ?user email: ?email }` |

A concept-state read is the only data access that crosses a concept boundary at read time,
which is what makes hard rule R1 enforceable by inspection of the sync
spec. Patterns A and B both work through the shared flow token — the
sync sees these bindings without any cross-concept read.

The full pattern catalogue, with worked examples, anti-patterns, and
03a audit guidance, is in [`SYNC_PATTERNS.md`](SYNC_PATTERNS.md).
In the sync's source file, patterns are documented in a "Where clause
patterns" table (see the [`templates/sync.md`](../../templates/sync.md)).
Stage 03a's coordination review scans this table for concept-state read rows.

## Input matching in the when clause

A `when` token may constrain the trigger action's **input values** as well
as action and outcome:

```
when {
    Web/request: [ route: "profile" ] => [ routed ]
}
then { ... }
```

This is the paper-faithful dispatch shape the reference implementation
uses — `when Requesting.request (path: "/my-files")` — and, since engine
v0.3.6, it is the preferred way to scope shared triggers by route (R15).
A `Rule` firing requires every constrained input key to be present with
the equal value. A `where`-clause `Guard` remains legal for comparisons a
literal when-matcher cannot express (non-literal operands, e.g. guarding
against a sibling's field).

What this is **not**: business branching. Route identity is transport
metadata authored by the chain table, not business state. Discrimination
over business state still belongs in concept outcomes (R3).

Deliberate divergence from the reference implementation: its `where`
accepts imperative filters (`frames.filter(count >= 10)`) and JSON payload
assembly, and calls rich concept query actions. CLAD's `where` is a
declarative bind/filter phase only — discrimination belongs in concept
outcomes, payload shapes in concept actions, and rich lookups in
`FanOut` + state reads. See
[`SYNC_PATTERNS.md`](SYNC_PATTERNS.md) and R3.

## Joins (multi-`when`)

The paper's first `when` is "a **multi-action join** selecting which
completed actions in the flow match specified patterns". CLAD realizes it
directly: a sync may declare several **named conjuncts**, each with its own
action, completion, and optional input matcher. The rule fires **once** when
*every* conjunct has a matching completion in the same flow token.

```
sync RespondWhenJoinListAndTagTag

when {
    list: Catalog/list: [ id: ?id ] => [ Listed ; id: ?id ]
    tag:  Tagging/tag:  [ id: ?id ] => [ Tagged ; id: ?id ]
}
where {
    bind ( list.id as ?listedId )
    bind ( tag.id as ?taggedId )
}
then {
    Web/respond: [ id: ?listedId ]
}
```

- The **first** conjunct is the primary trigger: its action id is the one
  recorded for dedup and as the emission's `parentActionId`; the joined
  emission's `causedBySync` is the rule name.
- Conjunct completion order is irrelevant — the engine indexes the rule
  under every conjunct and fires once all have committed in the flow.
- Bindings name a conjunct explicitly: `name.field` reads that conjunct's
  completion field (Pattern B), `name.param` its invocation input
  (Pattern A). See [`SYNC_PATTERNS.md`](SYNC_PATTERNS.md).
- A single *unnamed* conjunct keeps the classic one-trigger form and naming.
- The joined name is
  `<Target><Action>[For<Scope>]WhenJoin<C1><A1><Out1>And<C2><A2><Out2>…`
  in declared conjunct order (deterministic).
- `generate_syncs.py` derives the joined skeleton and stem from the chain
  table's composite `When`. A rule may also be **hand-authored** with the
  same stem — parity compares the stem, not the emitter (`verify_sync_
  implementation_parity.py`), so both paths satisfy the gate.

This is code-free (R3): the join is data on the rule, not imperative
matching logic. It is **not** the declined in-`where` query/filter surface.

## How syncs fan out — the Frames model

A sync doesn't fire once per `when` match. It fires once per **frame** —
each distinct set of variable bindings that satisfies the `where` clause.
This is the same model used by Eagon Meng's `sync-blank` reference
implementation and the WYSIWID paper's predicate semantics.

**Origin of the term.** "Frames" comes from the paper (predicate
semantics over the causal flow) and its authors' own machine-readable
realization — the MIT 61040 `conceptbox` engine, whose `Frames` type the
implementation doc calls "a `Record<symbol, unknown>` binding set, one
`then`-fire per frame" (`conceptbox/design/background/implementing-synchronizations.md`).
CLAD's engine realizes the same intent as plain `Map<String, Object>`
frames in [`WhereEvaluator`](../../reference-impl/legible-engine/src/main/java/dev/legible/engine/WhereEvaluator.java)
— deliberately *without* conceptbox's `frames.query/filter/collectAs`
imperative API, whose expressive power CLAD declines in `where` (see
§"Input matching in the when clause" and the non-adoptions in
`SYNC_ENGINE_EVOLUTION.md`).

A frame is simply one row in the `where` clause's result set. If a
`where` clause queries "all followers of this post" and finds three
followers, the result set has three rows, which means three frames. The
`then` clause emits one invocation per frame.

```
sync NotifyFollowersOnComment

when {
    Comment/create: [ post: ?post ] => [ CREATED ]
}
where {
    // This query produces one row per follower → N frames
    Follow: { ?f user: ?user . target: ?post }
}
then {
    Notification/notify: [ to: ?user, message: "New comment" ]
}
```

If the post has 3 followers, this sync fires 3 `Notification/notify`
invocations — one per frame. The frame set IS the fan-out.

Two syncs that would be separate event handlers in a procedural model
collapse into one declarative rule: the `where` clause handles the
fan-out, and `then` handles each resulting frame. This is why syncs
never contain loops or `for` statements — the iteration is implicit in
the query result.

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

Reads fields from named concept regions. This is a concept-state read — every such
read is recorded in the Stage 03a coordination review. The syntax mirrors
relation patterns: a subject variable, a semicolon-separated list
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
declarative equivalent of `GROUP BY`. Without `?_eachthen`, a
sync whose `where` produces multiple bindings (e.g. one per tag) would
fire the `then` clause once for each binding, which would produce a
response per tag instead of one response per article.

### Collect (declarative aggregation)

`collect` gathers the values a declarative source yields into **one `List`
value**, bound by the enclosing `bind`:

```
where {
    collect ( Tagging: { ?article tags: ?tag } as ?tags )
    collect distinct ( Tagging: { ?article tags: ?tag } as ?tags )
    collect by ?article ( Tagging: { ?article tags: ?tag } as ?tags )
}
```

- `collect ( <source> as ?var )` — every value the source produces, in one
  `List`.
- `collect distinct ( <source> as ?var )` — de-duplicated and
  deterministically ordered.
- `collect by ?groupKey ( <source> as ?var )` — frames grouped by
  `?groupKey`, binding one `List` per group (the frame-set analogue of
  `?_eachthen`).
- `scan(Concept, predicate)` reads every value of a predicate across a
  concept's region as one `List`; `distinct`/`collect` wrap any source.
- `absent ( Concept ; ?subject ; predicate )` is the **negative** state pattern:
  it keeps a frame only if the subject has no such value, binding nothing. It is
  how a rule says "the ones that do not have X" — the member's *remaining open*
  loans, the unshipped orders — which no enumerating source can express. It
  fails closed on an unbound subject. See
  `maintenance/engine-absent-state-guard.md`.

This is the declarative analogue of the reference implementation's
`collectAs`, and is deliberately **not** its imperative
`frames.query/filter/collectAs` API: there are no in-`where` filters, JSON
assembly, or query DSL — `collect` only gathers values a source already
produces (R3).

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
one intentional divergence:

| Area | Paper | CLAD |
|---|---|---|
| Outcome matching | `Concept/action: [ input ] => []` (empty brackets for no-output outcomes) | `Concept/action: [ input ] => [ outcomeName ]` (inlines the outcome name in the arrow's right side) |

Otherwise, the `when { }` / `where { }` / `then { }` block structure,
`Concept/action:` namespace qualifiers (including the `Web/request`
bootstrap entry action), `?variable` bindings, `bind()`
and `OPTIONAL` constructs, and `?_eachthen` aggregation all follow the
paper's design.

## Authoring a sync (for agents)

When stage `03_syncs/` runs, the agent should produce one
`<name>.sync.md` per coordination rule identified by the use case and
the concept specs. Use [`templates/sync.md`](../../templates/sync.md).
Each sync must reference, in a `Cites` section, the use-case scenario
that demands it; this is what makes stage 5 verification possible.
