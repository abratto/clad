# Concepts

A **concept** is the unit of legibility in a WYSIWID system. It is a
small, independent state machine that models one user-facing capability.
Concepts are *polymorphic*: they do not know whose data they are managing
or what the surrounding system looks like. They are *self-contained*:
their state is theirs alone, and they expose behaviour only through
named actions.

## Anatomy

Every concept spec has five sections.

### 1. Concept header

```
concept PasswordAuth [UserId]
purpose
    to verify a principal by userId + password
```

The `concept` keyword announces a spec in the WYSIWID language. The
name is a **noun** in PascalCase, referring to a capability, not an
entity. (`User` is fine because there is something called a user;
`UserService` is not, because the service-ness is incidental.)

Type parameters in brackets make the concept polymorphic: `PasswordAuth
[UserId]` says `PasswordAuth` can manage credentials for any kind of
user identifier without depending on the `User` concept.

### 2. State — relational notation

The data the concept owns, expressed as typed relations with multiplicity
annotations. This notation is adapted from the WYSIWID paper (Meng &
Jackson, Onward! 2025), which uses the form `field: SubjectType -> FieldType`.
Multiplicity annotations are a CLAD extension required by Stage 03b's
CSDP data modeling.

```
passwordHash: UserId -> PasswordHash        -- mandatory
failedAttempts: UserId -> Int               -- mandatory, default 0
lockedUntil: UserId -> Timestamp            -- optional
```

Multiplicity annotations:
- `mandatory` — every instance of the subject must have this field
- `optional` — may be absent
- `conditional mandatory: <condition>` — mandatory only when the condition holds
- `zero or more` — multi-valued relation

For stateless concepts:
```
*None.* <ConceptName> is stateless. All data is read on-demand from
flow tokens and upstream action payloads.
```

State is **private** to the concept. No other concept may read it directly
(hard rule R1). The only legal cross-concept read is a concept-state read in the `where`
clause in a sync spec.

**The subject type is an identifier type, not the concept itself.** Every
state field ranges over a *set* of individuals: `username: UserId -> String`
says "for each user, a username." The thing to the left of the arrow is the
individual's identity type (`UserId`), never the concept's own name (`User`).
A state block that lists *untyped* field names — `userid, username,
password, email` — is the object-oriented trap: it models one object's
instance variables, and then an action like `authenticate(username, password)`
cannot answer "which user?". The concept owns the *set*; the subject is the
*individual*. Typed fields in any form are fine — a relation
(`username: UserId -> String`), a collection (`leadLog: List<LeadRecord>`), a
map (`attorneyStatus: Map<AttorneyId, Availability>`) — what is never fine is a
bare name with no type at all. (`verify_concept_state_relational.py` enforces
this at Stage 02.)

**Separate views, even when they share a noun.** A `User` concept should not
hold `username, password, email, displayname` together — those belong to
different capabilities (naming, authentication, profiling) and different
owners. Tease them apart: `username` to a naming concept, `password` to
`PasswordAuth`, `email`/`displayname` to a profile concept. If two fields serve
different purposes, they are two concepts' state, not one concept's.

### 3. Actions — case-split notation

The verbs the concept exposes. Each action lists every possible output as
a separate indented case-split block. This makes exhaustiveness visible
at a glance and maps directly to the TDD case-split in Stage 04.

Two formats are available:

**Format A — precondition/postcondition** (for actions whose failures are
pure state-guard violations). A failed precondition causes **refusal**
(`:outcome "refused"`) — the action does not execute, no state changes,
and syncs match on `[ refused ]`. Use this when the action either succeeds
fully or is meaningless to attempt.

**Format B — case-split error outcomes** (for actions whose failures are
state-mutating). Each failure is a named outcome (`[ ok ]`, `[ error:
"badPassword" ]`). Use this when a failure pathway still mutates state
(e.g. incrementing a counter).

Format A example (precondition refusal):

```
lookupByUsername [ username: String ] => [ userId: UserId ]
    precondition {
        username in Dom(State.username)
    }
    postcondition {
        State.username[userId] == username
    }
    no state change
    flow token: { action: "User.lookupByUsername", username, userId, outcome: "FOUND" }
```

Format B example (case-split error outcomes):

```
verify [ userId: UserId ; password: String ] => [ ok ]
    password matches credentials[userId] and account is not locked
    clears failedAttempts[userId]
    flow token: { action: "PasswordAuth.verify", userId, outcome: "ok" }

verify [ userId: UserId ; password: String ] => [ error: "invalidPassword" ]
    userId is registered but password did not match
    increments failedAttempts[userId]; if counter reaches threshold,
    sets lockedUntil[userId] to now + 15 minutes

verify [ userId: UserId ; password: String ] => [ error: "locked" ]
    lockedUntil[userId] is in the future
    no state change

verify [ userId: UserId ; password: String ] => [ error: "unknownPrincipal" ]
    userId has no registered credential
    no state change
```

Rules:
- One block per outcome — do not collapse two outcomes into one block (R9).
- **Precondition failures are refusals, not error outcomes.** If a failure
  does not mutate state, use Format A with a `precondition` block. If a
  failure does mutate state (e.g. incrementing a counter), use Format B
  with a named `error:` outcome.
- The flow token is declared in the happy-path block only.
- The password is **never** in the flow token.
- Actions are the *only* way the outside world influences the concept.

### 4. Operational principle — sync notation trace

A witness trace of the typical happy path, written in `after`/`then`
sync notation. This is the WYSIWID heart of the spec: if a reader can
follow the operational principle, they understand the concept.

The notation mirrors Stage 03 sync files, making it directly traceable:
`after` = `when`, `then` = `then`. Happy path only — no branching.

```
Operational principle
---------------------
after  PasswordAuth/setPassword: [ userId: u ; password: p ] => [ ok ]
then   PasswordAuth/verify:      [ userId: u ; password: p ] => [ ok ]
-- five consecutive failures lock the account --
then   PasswordAuth/verify:      [ userId: u ; password: wrong ] => [ error: "invalidPassword" ]
-- (× 5) --
then   PasswordAuth/verify:      [ userId: u ; password: p ]     => [ error: "locked" ]
```

## What a concept must not do

- **Reference another concept.** Not by import, not by name, not by
  shared schema. If `PasswordAuth` needs to know which `User` is
  attempting, the `User` is passed in as an opaque `userId`; the
  identity of the value is the calling sync's problem.
- **Own an HTTP endpoint.** Only `Web` (or the equivalent bootstrap
  concept) exposes HTTP. A concept's actions are local function calls.
- **Cross persistence boundaries.** When persistence applies, each
  concept owns one storage region (e.g. one named graph, one schema,
  one set of tables). Reading another concept's region is a violation.

## What a concept may do

- Maintain whatever internal data structures its job requires.
- Emit flow tokens on every action.
- Define helper functions, types, and tests *internally*.

## Notation provenance

The state notation (`field: SubjectType -> FieldType`) is drawn from
the WYSIWID paper (Meng & Jackson, Onward! 2025), where Section 4
defines it with the form `field: Type -> Type`. CLAD adapts this to
`field: SubjectType -> FieldType` and adds multiplicity annotations
(as `-- mandatory | optional | ...`) for use in Stage 03b data modeling.

The case-split action notation (`actionName [ params ] => [ outputs ]`)
and the `after`/`then` operational principle trace are also from the
paper (Section 4). The underlying relational model owes a debt to
Alloy (Jackson, *Software Abstractions*, MIT Press 2006/2012). Neither
the Alloy toolchain nor the Alloy Analyzer is required — both notations
are used for precision and human readability only.

See `../reference/CITATIONS.md` for full attributions.

## Relationship to the Meng & Jackson paper

CLAD's concept specification language is aligned with the paper's
Section 4 with three intentional divergences:

| Area | Paper | CLAD |
|---|---|---|
| Web actions | `Web/request` | `Web/handle` — more precise about the responsibility ("handle" an HTTP request, not just "request") |
| Multiplicity annotations | Not present | Added as `-- mandatory / optional / ...` comments for Stage 03b data modeling |
| Operational principle | Unqualified action names: `after set [...]` | Fully qualified: `after PasswordAuth/setPassword: [...]` — maintains traceability to the concept boundary |

## Is it a concept? — heuristics for agents

When deciding what belongs as its own concept (Stage 01a responsibility
map), use these tests. If you answer "no" to any of them, the thing
probably shouldn't be its own concept.

### 1. One distinct user-facing purpose

A concept does exactly one thing a user cares about. `Password` handles
authentication. `Upvote` handles expressing interest. `Trash` handles
soft-deletion. If you're tempted to add a second, unrelated action,
split it:

| ✅ Good concept | ❌ Too much |
|---|---|
| `Password` — authenticate, reset | `Account` — authenticate, set profile, manage billing, send invites |
| `Article` — CRUD, slug management | `ArticleManager` — CRUD, SEO, analytics, versioning, social sharing |

**Heuristic:** If you describe the concept in conversation and need the
word "and," you might need two concepts. "It handles authentication" →
one concept. "It handles authentication and profile management" → two.

### 2. Self-contained state

A concept owns all the state it needs to operate. It never reads another
concept's state directly. If you need another concept's data, you either
(a) accept it as an input parameter from the sync that called you, or
(b) do a concept-state read in the sync's `where` clause.

### 3. Polymorphic by default

Concepts use opaque type parameters and identifiers. `Password` takes a
`[UserId]` — it doesn't know or care what a `User` is. `Comment` takes a
`[TargetId]` — it attaches to a post, an article, a profile, whatever.
If your concept imports another concept's types, you're doing it wrong.

### 4. Small enough for one context window

A concept spec (plus the syncs that reference it) should fit in one LLM
context window. If an agent needs to load other concepts to understand
this one, the concept is too large or too entangled.

### 5. Not a sync

If the thing you're modeling is purely a coordination rule ("when X
completes, then Y"), it's a sync (Stage 03), not a concept. Concepts
do things. Syncs connect things.

```
✅ Concept: Article — creates, reads, updates, deletes articles
✅ Sync: when Article/create[CREATED] → Notification/notify { to: ?user }
❌ Concept: ArticleCreationNotifier (this is just a sync)
```

### 6. Independent lifetime

A concept should be removable without breaking other concepts' internal
invariants. If you can delete this entire capability from the product
and the remaining concepts' state machines are still valid, it's a
proper concept boundary.

```
✅ You can remove Upvote or Tagging from an article app without
   affecting Article's ability to create, edit, or delete.
❌ If removing "password reset" breaks Password's authentication
   state machine, they should be one concept, not two.
```

### 7. Not any of these

These constructs are NOT concepts and belong elsewhere in CLAD:

| Construct | Why not a concept | Where it belongs |
|---|---|---|
| Cross-concept workflow | Coordinates multiple purposes | Sync (Stage 03) |
| Database table / DTO | No behavioral purpose | Internal concept implementation |
| API endpoint / route | Transport mechanism | Web concept + infrastructure |
| UI component / widget | Visual layout | Frontend (outside CLAD scope) |
| Pure calculation | No internal state | Helper utility in concept |
| Data structure | Passed between actions, not owned | Type parameter or payload |

### 8. State over a set, not fields of an object

A concept's state must be relations over a *set* of individuals, never a
list of one object's untyped instance variables. The subject of a relation is
an identifier type (`UserId`), not the concept's own name (`User`).

```
✅ PasswordAuth state:  passwordHash: UserId -> PasswordHash
✅ LeadLog state:       leadLog: List<LeadRecord>          (a collection)
✅ TriageQueue state:   attorneyStatus: Map<AttorneyId, Availability>  (a map)
❌ User state:          userid, username, password, email, displayname
❌ Account state:       username: Account -> String
```

The trap is a **bare field name with no type at all** — the `userid,
username, password` list models one object's instance variables, so an action
like `authenticate(username, password)` cannot say "which user?". Typed fields
in any form — a relation, a collection, a map, a subject arrow to a struct —
are fine; only the untyped list is the smell. The second smell is a relation
whose subject type is the concept's own name (`Account -> String`), which
models one object rather than a set. This is the single most common
object-oriented confusion (see Daniel Jackson, *Why concepts aren't objects*).
`verify_concept_state_relational.py` fails the Stage 02 gate on both.

## Decision flowchart for agents

When the responsibility map (Stage 01a) asks "is this a concept?",
walk each candidate through these four gates:

```
Candidate feature F
         │
    ┌────┴────┐
    │ 1. Does F maintain its own state and expose actions to
    │    modify that state?
    └────┬────┘
     No  │  Yes
         ▼
    Not a concept — helper function, payload type, or config.

         │
    ┌────┴────┐
    │ 2. Can F's purpose be stated in one sentence without "and"?
    └────┬────┘
     No  │  Yes
         ▼
    Split F into two or more concepts (F₁, F₂...).

         │
    ┌────┴────┐
    │ 3. Does F directly import or reference another concept
    │    (beyond opaque type IDs)?
    └────┬────┘
    Yes  │  No
         ▼
    Refactor: remove direct imports, use generic IDs, move
    interaction to a sync.

         │
    ┌────┴────┐
    │ 4. If we deleted F tomorrow, would the remaining concepts
    │    still function correctly?
    └────┬────┘
     No  │  Yes
         ▼
    F's state is entangled — it's not a clean concept boundary.
    Merge it with the concept it depends on, or re-split.
         │
    ✅ Valid concept. Write it up in the responsibility map.
```

## Authoring a concept (for agents)

When stage `02_concepts/` runs, the agent should produce one
`<Name>.concept.md` per concept identified in the use case. Use
[`templates/concept.md`](../../templates/concept.md). Stop at the gate;
the human will edit before stage `03_syncs/` runs.
