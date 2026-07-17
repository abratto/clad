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
(hard rule R1). The only legal cross-concept read is a Pattern D `where`
clause in a sync spec.

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

## Authoring a concept (for agents)

When stage `02_concepts/` runs, the agent should produce one
`<Name>.concept.md` per concept identified in the use case. Use
[`templates/concept.md`](../../templates/concept.md). Stop at the gate;
the human will edit before stage `03_syncs/` runs.
