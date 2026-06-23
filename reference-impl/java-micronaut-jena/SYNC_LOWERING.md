# Sync Lowering — Java/Jena/Micronaut

This document is the **profile-specific lowering contract** from an
approved Stage 03 sync spec to an executable `SyncAgent` subclass in the
Java/Jena/Micronaut reference profile.

It is not a global CLAD rule. It applies only when a feature selects the
Java/Jena profile under `reference-impl/java-micronaut-jena/`.

The business source of truth remains upstream artefacts:

- Stage 02 concept specs
- Stage 03 sync specs
- Stage 04b SPEC slices
- Stage 04c expected authored action chain
- approved red sync tests from Stage 04e-red

If this lowering contract appears to conflict with those upstream
artefacts, the upstream artefacts win and implementation must stop.

## Preconditions

Before lowering one sync, confirm all of these:

- There is exactly one approved Stage 03 `*.sync.md` file for the rule.
- Its `when` and `then` signatures match Stage 02b and Stage 02 exactly.
- Any needed Pattern A names are declared on the approved trigger token.
- The relevant action signatures and outcome enums exist in `04b_spec/`.

## Deterministic class mapping

For this profile, one approved Stage 03 sync lowers to exactly one Java
class under `<APP_PACKAGE_ROOT>.syncs` that:

- is `final`
- extends `SyncAgent`
- has only injected dependencies needed by the base profile shape
- implements `syncName()`, `trigger()`, `whereClause()`, and
  `thenBindings()`

Use the approved sync name for the class name with standard Java class
capitalization. Use lower camel case for `syncName()`.

## SPARQL fragment construction

Use Java text blocks for `whereClause()` and `thenBindings()` fragments.
Interpolate IRI constants via `.formatted()`.

When a sync needs a non-outcome string literal such as a route name,
message text, or other discriminator, declare it as a
`private static final String` constant and bind it through
`ParameterizedSparqlString`. In the CLAD reference profile, prefer the
base-class hook `parameterizeSparql(...)` instead of rebuilding the
outer update manually in each subclass.

Keep outcome literals explicit in the SPARQL text. Do not parameterize
`"FOUND"`, `"OK"`, `"GRANTED"`, and similar outcome values, because the
lowering contract needs those branches to stay visibly one-to-one with
the approved SPEC outcomes.

### Text block shape

whereClause (completion-shaped trigger — outcomes and fields are direct
properties of the action node):

```java
@Override
protected String whereClause() {
  return """
    ?_when_1 :concept <%s> ;
         :name    "lookupByUsername" ;
         :flow    ?_flow ;
         :outcome "FOUND" ;
         :userId  ?_userId .
    """.formatted(UserConcept.IRI);
}
```

whereClause (bootstrap-shaped trigger — matches the Web request action's
input node):

```java
@Override
protected String whereClause() {
  return """
    ?_when_1 :concept <%s> ;
         :name    "request" ;
         :input   ?_inp ;
         :flow    ?_flow .
    ?_inp :route ?_route ;
        :copyId ?_copyId ;
        :memberId ?_memberId .
    """.formatted(WEB_IRI);
}
```

thenBindings (non-respond — input arguments as a blank node):

```java
@Override
protected String thenBindings() {
  return """
    ?_then_1 :concept <%s> ;
         :name    "grant" ;
         :input   [ :userId ?_userId ] .
    """.formatted(SessionConcept.IRI);
}
```

thenBindings (respond — status code and payload fields as blank-node
properties):

```java
@Override
protected String thenBindings() {
  return """
    ?_then_1 :concept <%s> ;
         :name    "respond" ;
         :input   [ :statusCode ?_statusCode ;
                    :sessionToken ?_sessionToken ] .
    """.formatted(WEB_IRI);
}
```

### Parameterized literals

```java
private static final String ROUTE = "borrow";

@Override
protected String parameterizeSparql(String sparql) {
  return bindLiteral(sparql, "_route", ROUTE);
}
```

The `?_route` variable in the text block is bound at execution time by
`ParameterizedSparqlString`. This keeps the fragment readable as pure
SPARQL while still centralizing rename-sensitive literals in Java
constants.

## Engine-owned SPARQL shape

`SyncAgent` assembles the outer `INSERT ... WHERE` shape for you. The
subclass contributes only two fragments:

- `whereClause()` — the trigger pattern plus any Pattern A/B/C/D bindings
- `thenBindings()` — the new downstream invocation rooted at `?_then_1`

Reserved variables owned by the engine:

- `?_when_1`
- `?_flow`
- `?_then_1`

Do not redefine those names.

### How the action graph is structured — plain triples vs. RDF-star

The action graph uses **two layers of triples** on each action node. Only
one of these layers is visible to sync `whereClause()` fragments.

**Plain triples (the sync layer).** Concept agents write action properties
as plain subject-predicate-object triples directly on the action IRI
node. These are what sync `whereClause()` fragments match against:

```sparql
INSERT DATA {
  GRAPH <action-graph> {
    <action-iri> :concept <concept-iri> ;
                 :name    "check" ;
                 :outcome "OK" ;
                 :userId  "ada-0001" .
  }
}
```

Sync `whereClause()` matches these plain triples:

```java
return """
  ?_when_1 :concept <%s> ;
           :name    "check" ;
           :flow    ?_flow ;
           :outcome "OK" ;
           :userId  ?_userId .
  """.formatted(PasswordAuthConcept.IRI);
```

**RDF-star annotation (the engine layer).** The engine wraps the `:outcome`
triple with an RDF-star annotation carrying the flow token. This creates
a second, separate triple in the graph that ties the outcome event to its
flow for archival and traceability. It does **not** replace the plain
`:outcome` triple — it annotates it:

```sparql
INSERT DATA {
  GRAPH <action-graph> {
    <action-iri> :outcome "OK" .                                        # ← plain, sync-visible
    << <action-iri> :outcome "OK" >> :flow <flow-token> .               # ← RDF-star, engine-only
  }
}
```

ConceptAgent writes this via `writeCompletion()`:

```java
// ConceptAgent.java (actual code)
sparql.append("    << <").append(invocation.actionIri()).append("> :outcome ")
      .append(NodeFmtLib.str(output.get("outcome").asNode(), (PrefixMap) null))
      .append(" >> :flow <").append(invocation.flowToken()).append("> .\n");
```

**What sync authors need to know:**

- The `?_flow` variable used in `whereClause()` comes from the engine-owned
  outer `INSERT ... WHERE` shape. Syncs bind it; do not redefine it.
- The RDF-star annotation is invisible to sync fragments. Syncs match the
  plain `:outcome` and field triples exactly as documented below.
- The only consumer of the RDF-star annotations is `ActionLog.archiveFlow()`,
  which moves completed action annotations between the active and archive
  graphs without touching the plain action property triples.

## Lowering algorithm

For each approved sync:

1. **Lower the trigger concept/action into `trigger()`.**
   Use the concept IRI and action name named by the approved `when`.
   Keep `outputStatus` null unless the dispatcher contract is explicitly
   extended to index by outcome.
2. **Lower the trigger match into `whereClause()`.**
   Match the authored action node, shared `?_flow`, and its direct
   `:outcome` and field properties. For the bootstrap exception, match
   the root request action's `:input` node and its properties instead
   (see Bootstrap handoff exception below).
3. **Lower the trigger outcome literally.**
   If the sync fires on `FOUND`, match `:outcome "FOUND"` directly on
   the action node. Do not rename, normalize, or infer synonyms.
4. **Lower each Stage 03 binding pattern deterministically.**
   Pattern A/B/C/D each have one mapping shape; see below.
5. **Lower the `then` target into `thenBindings()`.**
   Emit exactly one `?_then_1` invocation with `:concept`, `:name`, and
   `:input` carrying a blank node.
6. **Lower the downstream arguments into the blank-node input.**
   Every argument in the approved `then` signature becomes one property
   on the `:input` blank node, using the exact upstream field names and
   literals.

## Pattern mapping

### Pattern A — trigger-token join

Stage 03 meaning:

```text
where: A: username = when.username
```

Java/Jena lowering:

- If the trigger is realized as an action completion, bind directly from
  that action node's properties (no `:output` indirection).
- If the trigger is the bootstrap handoff exception, bind from the root
  request action's `:input` node.

Completion-shaped example:

```java
"""
?_when_1 :outcome "FOUND" ;
    :username ?_username .
"""
```

Bootstrap-shaped example:

```java
"""
?_when_1 :input ?_web_inp ;
         :flow  ?_flow .
?_web_inp :route ?_route ;
          :username ?_username .
"""
```

### Pattern B — flow-sibling join

Stage 03 meaning:

```text
where: B: userId = result_of(User.lookupByUsername).userId
```

Java/Jena lowering:

- Match the prior action node in the same `?_flow`.
- Read the needed field as a direct property of that action node (outcome
  and data fields are properties of the action, not of a separate output
  node).

Example:

```java
"""
?_lookup :concept <...User...> ;
         :name    "lookupByUsername" ;
         :flow    ?_flow ;
         :outcome "FOUND" ;
         :userId  ?_userId .
"""
```

### Pattern C — sync constant

Stage 03 meaning:

```text
where: C: statusCode = 200
```

Java/Jena lowering:

- Declare the constant as a `private static final String` field.
- Reference a bindable variable in the SPARQL fragment.
- Bind the literal value via `bindLiteral(...)` in `parameterizeSparql(...)`.

Example in `thenBindings()`:

```java
"""
?_then_1 :input [ :statusCode ?_statusCode ] .
"""
```

Example in `parameterizeSparql(...)`:

```java
private static final String STATUS_200 = "200";

@Override
protected String parameterizeSparql(String sparql) {
  return bindLiteral(sparql, "_statusCode", STATUS_200);
}
```

### Pattern D — concept-state join

Stage 03 meaning:

```text
where: D: dueDate = state_of(Loan).dueDate
```

Java/Jena lowering for this profile:

- Pattern D is allowed only when the approved Stage 03 sync and Stage 03a
  dependency review explicitly justify it.
- The read happens in the sync `whereClause()`, never inside concept
  Java code.
- Match the owning concept's named graph directly in SPARQL; do not call
  another concept class and do not read another concept graph from inside
  a concept agent.

Example shape:

```java
"""
GRAPH <%s> {
  ?loan :loanId ?_loanId ;
        :dueDate ?_dueDate .
}
""".formatted(RdfVocabulary.conceptGraph("loan"))
```

## Bootstrap handoff exception

Stage 02b/03 model the transport entry as:

```text
1 | Web/request[...] -> Web.handle | ... | Routed(...)
2 | Web.handle[Routed(...)] -> <Concept>.<action> | ...
```

In this Java/Jena profile, the runtime transport adapter does not persist
an additional completed `Web.handle` action node. The first sync is
therefore realized against the root `Web/request` action's input node.

That is the only lowering exception to keep in mind:

- methodology level: the first sync is the row-2 handoff from `Web.handle`
- Java/Jena runtime level: the sync matches the persisted `Web/request`
  action that bootstrapped the flow

All non-bootstrap syncs still lower from completed action outcomes (now
direct `:outcome` properties on the action node).

## Sink sync lowering (`Web.respond`)

Sink syncs lower exactly like any other sync. The only difference is
their `then` target concept is the bootstrap concept IRI used by the
transport adapter.

Rules:

- status code literals are bound via `bindLiteral(...)` in
  `parameterizeSparql(...)` and referenced in `thenBindings()` via a
  bindable variable
- response payload fields come only from approved upstream outcomes or
  approved constants
- do not assemble ad hoc payload objects in Java; write the RDF input
  triples that the `Web` concept expects

Example:

```java
"""
?_then_1 :concept <%s> ;
         :name    "respond" ;
         :input   [ :statusCode ?_statusCode ;
                    :sessionToken ?_sessionToken ] .
""".formatted(WEB_IRI)
```

## Worked derivation slice — successful login

### Stage 02a concept set

| Concept | Owned capability |
|---|---|
| `Web` | transport entry/exit |
| `User` | look up a principal by username |
| `PasswordAuth` | check a presented credential |
| `Session` | grant a session token |

### Stage 02b rows

```text
1 | Web/request[POST /login] | Web.handle | ... | Routed(username, password)
2 | Web.handle[Routed(username, password)] | User.lookupByUsername | username | Found(userId), NotFound
3 | User.lookupByUsername[Found(userId)] | PasswordAuth.check | userId, password | Ok(userId), BadPassword, Locked
4 | PasswordAuth.check[Ok(userId)] | Session.grant | userId | Granted(sessionToken)
5 | Session.grant[Granted(sessionToken)] | Web.respond[200] | status: 200, body: { sessionToken } | Sent
```

### Stage 03 syncs

```text
LookupUserForLogin:
  when:  Web.handle[Routed(username, password)]
  where: A: username = when.username
  then:  User.lookupByUsername(username)

GrantSessionForLogin:
  when:  PasswordAuth.check[Ok(userId)]
  where: B: userId = result_of(PasswordAuth.check).userId
  then:  Session.grant(userId)

RespondLoginSuccess:
  when:  Session.grant[Granted(sessionToken)]
  where: B: sessionToken = result_of(Session.grant).sessionToken
  then:  Web.respond(statusCode=200, sessionToken)
```

### Java/Jena lowering

`GrantSessionForLogin.whereClause()`:

```java
return """
  ?_when_1 :concept <%s> ;
       :name    "check" ;
       :flow    ?_flow ;
       :outcome "OK" ;
       :userId  ?_userId .
  """.formatted(PasswordAuthConcept.IRI);
```

`GrantSessionForLogin.thenBindings()`:

```java
return """
  ?_then_1 :concept <%s> ;
       :name    "grant" ;
       :input   [ :userId ?_userId ] .
  """.formatted(SessionConcept.IRI);
```

`RespondLoginSuccess.thenBindings()`:

```java
return """
  ?_then_1 :concept <%s> ;
       :name    "respond" ;
       :input   [ :statusCode ?_statusCode ;
                  :sessionToken ?_sessionToken ] .
  """.formatted(WEB_IRI);
```

That is the intended mechanical path: approved chain row -> approved
sync spec -> approved SPEC/test surface -> one `SyncAgent` subclass.
