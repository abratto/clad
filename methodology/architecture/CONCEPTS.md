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

### 2. State

The data the concept owns. Described in plain prose plus a small typed
schema. This is the *only* state the concept has access to.

```
State
-----
- credentials: Map<UserId, PasswordHash>
- failedAttempts: Map<UserId, Int>
```

State is private to the concept. No other concept may read it.

### 3. Actions

The verbs the concept exposes. Each action lists:

- **inputs** (typed)
- **outputs** (typed, including failure modes)
- **effect on state** (in prose)
- **flow-token contribution** (what fields the emitted flow token carries)

```
Action: verify(userId, password) -> Ok | InvalidPassword | Locked
  - Reads credentials[userId].
  - On Ok: clears failedAttempts[userId].
  - On InvalidPassword: increments failedAttempts[userId]; if it crosses
    threshold, returns Locked thereafter.
  - Flow token: { action: "PasswordAuth.verify", userId, outcome }.
```

Actions are the *only* way the outside world (other concepts via syncs,
or `Web` via the HTTP surface) influences the concept.

### 4. Operational principle

A short prose story of how the concept is meant to be used: a typical
sequence of actions and what the user observes. This is the heart of
WYSIWID — if a reader can follow the operational principle, they
understand the concept.

```
Operational principle
---------------------
A user registers a credential by calling `register(userId, password)`.
Later, they prove identity by calling `verify(userId, password)`. After
N consecutive InvalidPassword outcomes the userId is Locked and further
verify calls return Locked until an out-of-band reset.
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

## Authoring a concept (for agents)

When stage `02_concepts/` runs, the agent should produce one
`<Name>.concept.md` per concept identified in the use case. Use
[`templates/concept.md`](../../templates/concept.md). Stop at the gate;
the human will edit before stage `03_syncs/` runs.
