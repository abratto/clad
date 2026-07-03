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
capitalization. The approved sync name is the Stage 03 file stem and
must follow CLAD's compressed rule grammar:

`When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]`

Use lower camel case for `syncName()`.

## SPARQL-star fragment construction

CLAD uses RDF-star/SPARQL-star (Jena 5.x native). Outcomes are written
twice with different roles: a plain `:outcome` triple prevents action
reprocessing, and an RDF-star annotation (`<< action :outcome value >>`)
ties the outcome to its flow token for sync matching and archival. Sync
`whereClause()` fragments match the star annotation directly.

Use Java text blocks for `whereClause()` and `thenBindings()` fragments.
Interpolate IRI constants via `.formatted()`.

### Template: whereClause (completion-shaped trigger)

Outcomes and non-outcome action fields are matched separately —
non-outcome fields (`:userId`, `:sessionToken`) are plain triples on
the action node; `:outcome` is matched inside the RDF-star annotation:

```java
@Override
protected String whereClause() {
  return """
    ?_when_1 :concept <%s> ;
             :name    "lookupByUsername" ;
             :userId  ?_userId .
    << ?_when_1 :outcome "FOUND" >> :flow ?_flow .
    """.formatted(UserConcept.IRI);
}
```

### Template: whereClause (bootstrap-shaped trigger)

Bootstrap triggers match the Web request action's `:input` node — no
outcome filtering:

```java
@Override
protected String whereClause() {
  return """
    ?_when_1 :concept <%s> ;
             :name    "request" ;
             :input   ?_inp ;
             :flow    ?_flow .
    ?_inp :route ?_route ;
         :username ?_username .
    """.formatted(WEB_IRI);
}
```

### Template: whereClause with variable outcome + FILTER

When a sync fires on multiple outcomes, match `:outcome` as a variable
inside `<< >>` and filter:

```java
@Override
protected String whereClause() {
  return """
    ?_when_1 :concept <%s> ;
             :name    "check" .
    << ?_when_1 :outcome ?_outcome >> :flow ?_flow .
    FILTER (?_outcome IN ("BAD_PASSWORD", "NO_CREDENTIAL"))
    """.formatted(PasswordAuthConcept.IRI);
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

The action graph uses **two layers of triples** on each completed action
node. They have separate jobs, and sync authors must use the right one.

**Plain triples (the reprocessing guard and field layer).** Concept
agents write action properties as plain subject-predicate-object triples
directly on the action IRI node. The plain `:outcome` triple prevents the
concept worker from reprocessing the same action; non-outcome fields are
also plain triples that syncs can bind:

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

Sync `whereClause()` matches non-outcome fields as plain triples, but
matches outcomes through the RDF-star annotation:

```java
return """
  ?_when_1 :concept <%s> ;
           :name    "check" ;
           :userId  ?_userId .
  << ?_when_1 :outcome "OK" >> :flow ?_flow .
  """.formatted(PasswordAuthConcept.IRI);
```

**RDF-star annotation (the sync and engine layer).** The engine wraps the
`:outcome` triple with an RDF-star annotation carrying the flow token.
This creates a second, separate triple in the graph that ties the outcome
event to its flow for sync matching, archival, and traceability. It does
**not** replace the plain `:outcome` triple — it annotates it:

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
sparql.append("    <").append(invocation.actionIri()).append("> :outcome ")
  .append(NodeFmtLib.str(outcomeNode.asNode(), (PrefixMap) null))
  .append(" .\n");

sparql.append("    << <").append(invocation.actionIri()).append("> :outcome ")
      .append(NodeFmtLib.str(output.get("outcome").asNode(), (PrefixMap) null))
      .append(" >> :flow <").append(invocation.flowToken()).append("> .\n");
```

**What sync authors need to know:**

- The `?_flow` variable used in `whereClause()` comes from the engine-owned
  outer `INSERT ... WHERE` shape. Syncs bind it; do not redefine it.
- Syncs match outcomes with RDF-star (`<< ?_when_1 :outcome "OK" >> :flow ?_flow`)
  and match non-outcome fields as plain triples on `?_when_1`.
- The plain `:outcome` triple exists to block reprocessing in
  `ConceptAgent.findPendingInvocations()`. Do not use it as the sync's
  outcome condition.

## RDF-star cookbook

These are the places that use RDF-star. Sync `whereClause()` fragments
use RDF-star for outcome conditions and plain RDF triples for non-outcome
fields; sync `thenBindings()` and concept state queries use plain RDF
triples.

### 1. Write an action completion (success outcome)

Location: `ConceptAgent.writeCompletion()`.

```java
// actionIri and flowToken are strings, output is Map<String,RDFNode>
sparql.append("INSERT DATA {\n");
sparql.append("  GRAPH <action-graph> {\n");
// Plain triples for action properties (sync-visible)
for (var entry : output.entrySet()) {
    sparql.append("    <").append(actionIri).append("> :")
          .append(entry.getKey()).append(" ")
          .append(NodeFmtLib.str(entry.getValue().asNode(), null))
          .append(" .\n");
}
// RDF-star annotation tying the outcome to its flow
sparql.append("    << <").append(actionIri).append("> :outcome ")
      .append(NodeFmtLib.str(output.get("outcome").asNode(), null))
      .append(" >> :flow <").append(flowToken).append("> .\n");
sparql.append("  }\n}\n");
```

Produces:

```sparql
INSERT DATA {
  GRAPH <https://clad.dev/actions> {
    <action-iri> :concept <https://clad.dev/concept/user> ;
                 :name    "lookupByUsername" ;
                 :outcome "FOUND" ;
                 :userId  "ada-0001" .
    << <action-iri> :outcome "FOUND" >> :flow <https://clad.dev/flow/uuid> .
  }
}
```

### 2. Write an error completion

Location: `ConceptAgent.writeError()`.

```sparql
INSERT DATA {
  GRAPH <action-graph> {
    <action-iri> :concept <concept-iri> ;
                 :name    "check" ;
                 :error   "Bad credentials" .
    << <action-iri> :outcome "error" >>
                            # no :flow — errors are not archived per-flow
  }
}
```

### 3. Archive a completed flow

Location: `ActionLog.archiveFlow()`.

```sparql
DELETE { GRAPH <active> {
    << ?a :outcome ?outcome >> ?p ?o .
} }
INSERT { GRAPH <archive> {
    << ?a :outcome ?outcome >> ?p ?o .
} }
WHERE  { GRAPH <active> {
    << ?a :outcome ?outcome >> ?p ?o .
    ?a :flow <flow-token> .
} }
```

This moves all RDF-star-annotated outcome annotations for a given flow
token from the active graph to the archive graph. The plain action
property triples stay in the active graph — only the `<< ... >>`
annotations are moved.

### 4. How to use RDF-star in syncs

Sync `whereClause()` must use RDF-star syntax for outcome conditions and
plain triples for non-outcome fields:

```java
/* CORRECT — RDF-star outcome plus plain field binding */
"""
?_when_1 :concept <%s> ;
         :name    "check" ;
         :userId  ?_userId .
<< ?_when_1 :outcome "OK" >> :flow ?_flow .
""".formatted(PasswordAuthConcept.IRI);
```

```java
/* WRONG — plain outcome in sync whereClause */
"""
?_when_1 :outcome "OK" ;
         :userId ?_userId .
"""
// This ignores the engine-owned flow annotation and can break route scoping.
```

Sync `thenBindings()` should also never use RDF-star. Write plain
triples with blank-node input:

```java
/* CORRECT — blank-node input */
"""
?_then_1 :concept <%s> ;
         :name    "grant" ;
         :input   [ :userId ?_userId ] .
""".formatted(SessionConcept.IRI);
```

### 5. Why RDF-star instead of blank-node reification

Before RDF-star, the engine used blank-node reification to attach flow
tokens to outcome events:

```sparql
# OLD (pre-star) — verbose, requires triple the triples
[a :subject <action> ; :predicate :outcome ; :object "FOUND"] :flow <token> .
```

RDF-star collapses this to a single readable line:

```sparql
# NEW (star) — compact, readable
<< <action> :outcome "FOUND" >> :flow <token> .
```

Jena 5.x supports RDF-star natively. The engine migrated in CHANGELOG.md.

## Concept implementation SPARQL patterns

Sync `whereClause()` / `thenBindings()` fragments are governed by the
previous sections. Concept agents have their own SPARQL patterns for
reading and writing state in their named graph. This section captures
the patterns that agents must follow when implementing `doXxx` handlers
inside a `ConceptAgent` subclass.

### SELECT — look up concept state

Use the **specific IRI** for the entity, not a generic `?entity` variable.
The lookup must target the exact entity, or it will match any entity in
the graph and always succeed.

```java
// CORRECT — targets the specific prescription IRI
String lookupSparql = "PREFIX p: <" + NS + ">"
    + " SELECT ?status WHERE { GRAPH <" + GRAPH + "> {"
    + "   <" + NS + "prescription/" + prescriptionId + "> p:status ?status ."
    + " } } LIMIT 1";

// WRONG — matches any prescription in the graph
String lookupSparql = "PREFIX p: <" + NS + ">"
    + " SELECT ?status WHERE { GRAPH <" + GRAPH + "> {"
    + "   ?prescription p:status ?status ."
    + " } } LIMIT 1";
```

Build the IRI by concatenating the concept's namespace and the
identifier:

```java
String entityIri = NS + "prescription/" + prescriptionId;
// produces: https://clad.dev/concept/prescription#prescription/rx-001
```

### UPDATE — modify concept state with `WITH <graph>`

Use the `WITH <graph>` form for SPARQL UPDATE. Avoid nesting
`GRAPH ?g {}` inside `DELETE {}` / `INSERT {}` blocks — `ParameterizedSparqlString`
interprets the nested graph variable as a parameter and produces parse
errors.

```java
// CORRECT — WITH <graph> syntax
String updSparql = "PREFIX p: <" + NS + ">"
    + " WITH <" + GRAPH + ">"
    + " DELETE { <" + NS + "prescription/" + prescriptionId + "> p:autoRefillEnabled ?old }"
    + " INSERT { <" + NS + "prescription/" + prescriptionId + "> p:autoRefillEnabled \"true\" }"
    + " WHERE { OPTIONAL { <" + NS + "prescription/" + prescriptionId + "> p:autoRefillEnabled ?old } }";
actionLog.update(updSparql);

// WRONG — nested GRAPH ?g inside DELETE/INSERT (ParameterizedSparqlString parse error)
String updSparql = "DELETE { GRAPH ?g { ?prescription p:autoRefillEnabled ?old } }"
    + " INSERT { GRAPH ?g { ?prescription p:autoRefillEnabled \"true\" } }"
    + " WHERE { GRAPH ?g { OPTIONAL { ?prescription p:autoRefillEnabled ?old } } }";
```

The `WHERE` clause must bind every variable used in `DELETE`. When the
property being updated might not exist yet (first write), use `OPTIONAL`
to handle the unbound case.

### Direct string building vs ParameterizedSparqlString

| Context | Recommended approach |
|---|---|
| Sync `whereClause()` / `thenBindings()` fragments | Java text blocks with `.formatted()` + `bindLiteral()` as documented in the SPARQL fragment construction section |
| Concept SELECT / UPDATE queries | **Direct string concatenation** — no `ParameterizedSparqlString`. Build the full SPARQL string with string concatenation (`+`), interpolating IRIs and values directly |
| Concept `seedXxx()` / test fixtures | Direct string concatenation with `INSERT DATA` |

Rationale: `ParameterizedSparqlString` adds a layer of indirection that
works well for simple SELECT queries but produces parse errors with
`DELETE/INSERT WHERE`, nested `GRAPH ?g`, or `OPTIONAL` inside `WHERE`.
The generated SPARQL from `ParameterizedSparqlString` can also silently
produce invalid syntax when mixing named-graph patterns with UPDATE
clauses. Direct string building avoids these issues entirely and keeps
the SPARQL visible at the construction site.

### `writeCompletion` — how outcomes reach sync `whereClause`

Concept actions signal their result through
`writeCompletion(invocation, Map.of(...))` or
`writeError(invocation, message)`:

```java
// Success outcome — each Map entry becomes a plain triple on the action node
writeCompletion(invocation, Map.of(
    "outcome", ResourceFactory.createStringLiteral("Ok"),
    "prescriptionId", ResourceFactory.createStringLiteral(prescriptionId),
    "autoRefillEnabled", ResourceFactory.createStringLiteral(autoRefillEnabled)));

// Error outcome — produces :outcome "error" + :error "message"
writeCompletion(invocation, Map.of(
    "outcome", ResourceFactory.createStringLiteral("NotFound")));
```

The sync's `whereClause()` must match these plain triples exactly.
Outcome names (`"Ok"`, `"NotFound"`, `"NotEligible"`) must match
character-for-character between the concept's `writeCompletion` and the
sync's `whereClause`. No synonyms, no renamings.

### Concept test fixtures — write test actions and read outcomes

Concept tests follow a three-part pattern:

**1. Write a test action into the action log:**

```java
private void writeSetAutoRefillAction(String flowToken, String actionIri,
        String prescriptionId, String autoRefillEnabled) {
    String sparql = "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n"
        + "INSERT DATA {\n"
        + "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n"
        + "    <" + actionIri + "> :concept <" + PrescriptionConcept.IRI + "> ;\n"
        + "                     :name    \"setAutoRefill\" ;\n"
        + "                     :input   [ :prescriptionId \"" + prescriptionId
        + "\" ; :autoRefillEnabled \"" + autoRefillEnabled + "\" ] ;\n"
        + "                     :flow    <" + flowToken + "> .\n"
        + "  }\n"
        + "}\n";
    actionLog.update(sparql);
}
```

**2. Poll and process the action:**

```java
concept.pollAndProcess("setAutoRefill");
```

**3. Read the outcome:**

```java
private String readOutcome(String actionIri) {
    List<Map<String, String>> rows = actionLog.select(
        "PREFIX : <" + RdfVocabulary.ACTION_SCHEMA_IRI + ">\n"
        + "SELECT ?outcome WHERE {\n"
        + "  GRAPH <" + RdfVocabulary.ACTION_GRAPH_IRI + "> {\n"
        + "    <" + actionIri + "> :outcome ?outcome .\n"
        + "  }\n"
        + "}\n");
    return rows.isEmpty() ? null : rows.get(0).get("outcome");
}
```

### Common antipatterns

| Antipattern | Why it fails | Correct approach |
|---|---|---|
| `?entity p:predicate ?val` without IRIs | Matches any entity in the graph — lookup always succeeds even when the target entity doesn't exist | Use the specific entity IRI in subject position |
| Nested `GRAPH ?g` inside `DELETE`/`INSERT` | `ParameterizedSparqlString` can't resolve nested `?g` in UPDATE triples | Use `WITH <graph>` syntax |
| `ParameterizedSparqlString` for complex UPDATEs | Silent parse errors on `DELETE/INSERT WHERE` with `OPTIONAL` | Use direct string concatenation |
| `setLiteral("new", "value")` with unbound `?old` | `?old` variable in DELETE clause requires WHERE binding, but falls through PSS | Use direct string concatenation to control variable binding |

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
?_when_1 :username ?_username .
<< ?_when_1 :outcome "FOUND" >> :flow ?_flow .
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
WhenWebHandleRoutedThenUserLookupByUsernameForLogin:
  when:  Web.handle[Routed(username, password)]
  where: A: username = when.username
  then:  User.lookupByUsername(username)

WhenPasswordAuthCheckOkThenSessionGrantForLogin:
  when:  PasswordAuth.check[Ok(userId)]
  where: B: userId = result_of(PasswordAuth.check).userId
  then:  Session.grant(userId)

WhenSessionGrantGrantedThenWebRespondForLogin:
  when:  Session.grant[Granted(sessionToken)]
  where: B: sessionToken = result_of(Session.grant).sessionToken
  then:  Web.respond(statusCode=200, sessionToken)
```

### Java/Jena lowering

`WhenPasswordAuthCheckOkThenSessionGrantForLogin.whereClause()`:

```java
return """
  ?_when_1 :concept <%s> ;
       :name    "check" ;
       :userId  ?_userId .
  << ?_when_1 :outcome "OK" >> :flow ?_flow .
  """.formatted(PasswordAuthConcept.IRI);
```

`WhenPasswordAuthCheckOkThenSessionGrantForLogin.thenBindings()`:

```java
return """
  ?_then_1 :concept <%s> ;
       :name    "grant" ;
       :input   [ :userId ?_userId ] .
  """.formatted(SessionConcept.IRI);
```

`WhenSessionGrantGrantedThenWebRespondForLogin.thenBindings()`:

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
