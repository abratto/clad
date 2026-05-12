# Concepts

A **concept** is the unit of legibility in a WYSIWID system. It is a
small, independent state machine that models one user-facing capability.
Concepts are *polymorphic*: they do not know whose data they are managing
or what the surrounding system looks like. They are *self-contained*:
their state is theirs alone, and they expose behaviour only through
named actions.

## Anatomy

Every concept spec has four sections.

### 1. Name and one-line purpose

```
# PasswordAuth — verify a principal by username + password
```

A concept name is a **noun**, in PascalCase, and refers to a capability,
not an entity. (`User` is fine because there is something called a user;
`UserService` is not, because the service-ness is incidental.)

### 2. State — Alloy-style relational notation

The data the concept owns, expressed as typed relations with multiplicity
annotations. This notation is drawn from Daniel Jackson's Alloy (see
`../reference/CITATIONS.md`) and used here without the Alloy toolchain —
it adds precision without requiring a model checker.

```
credentials(userId: UserId) -> passwordHash: PasswordHash   -- mandatory
failedAttempts(userId: UserId) -> count: Int                -- mandatory, default 0
lockedUntil(userId: UserId) -> timestamp: Timestamp         -- optional
```

Multiplicity annotations:
- `mandatory` — every instance of the subject must have this field
- `optional` — may be absent
- `conditional mandatory: <condition>` — mandatory only when the condition holds
- `zero or more` — multi-valued relation

For stateless concepts:
```
*None.* TasteMatch is stateless. All data is read on-demand from
flow tokens and upstream action payloads.
```

State is **private** to the concept. No other concept may read it directly
(hard rule R1). The only legal cross-concept read is a Pattern D `where`
clause in a sync spec.

### 3. Actions — case-split notation

The verbs the concept exposes. Each action lists every possible output as
a separate indented case-split block. This makes exhaustiveness visible
at a glance and maps directly to the TDD case-split in Stage 04.

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

The relational state notation (`relation(subject) -> field: Type -- multiplicity`)
is adapted from Alloy (Jackson, *Software Abstractions*, MIT Press 2006/2012).
The case-split action notation and `after`/`then` operational principle trace
are drawn from the WYSIWID paper (Meng & Jackson, Onward! 2025) and
first applied in full in `abratto/tastetag`. Neither the Alloy toolchain
nor the Alloy Analyzer is required — the notation is used for precision
and readability only. See `../reference/CITATIONS.md`.

## Authoring a concept (for agents)

When stage `02_concepts/` runs, the agent should produce one
`<Name>.concept.md` per concept identified in the use case. Use
[`templates/concept.md`](../../templates/concept.md). Stop at the gate;
the human will edit before stage `03_syncs/` runs.
