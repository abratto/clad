# Jena version upgrade — align in-memory parser with Fuseki

## Problem

The reference-impl uses Jena 5.2.0 whose in-memory SPARQL parser accepts
`<< >>` RDF-star syntax in `INSERT DATA` templates via raw `StringBuilder`.
Apache Jena Fuseki 6.x (remote deployment) rejects this syntax — it treats
bare `<< >>` terms in DELETE templates as blank nodes. This means code that
passes `mvn test` against in-memory Jena fails at deploy time against Fuseki.

**Current stopgap (v0.1.1):** R21 rule in AGENTS.md + CODE_STYLE.md doc
telling agents to use programmatic APIs for Fuseki. RemoteStorage already
skips RDF-star annotation triples in archive. Split-brain: in-memory tests
use one pattern, Fuseki requires another.

## Root cause

Jena parser version mismatch. In-memory Jena 5.2.0 and Fuseki 6.x have
different SPARQL parsing profiles for RDF-star/SPARQL-star syntax.

## Solution

1. **Bump Jena version** in `reference-impl/java-micronaut-jena/pom.xml`
   to match Fuseki's parsing profile (≥ 5.3.0 or 6.x, TBD by testing).

2. **Migrate completion writes** in `ConceptAgent.writeCompletion()` and
   `PredicateConceptAgent.writeCompletionSparql()` from raw `StringBuilder`
   to `ParameterizedSparqlString.asUpdate()` with
   `NodeFactory.createTripleNode()` for the RDF-star annotation.
   Canonical pattern from Jena docs:
   ```java
   var pss = new ParameterizedSparqlString();
   pss.setNsPrefix("", schema);
   pss.setCommandText("INSERT DATA { GRAPH ?g { ?reified :flow ?tok } }");
   pss.setIri("g", graphIri);
   pss.setParam("reified", NodeFactory.createTripleNode(innerTriple));
   pss.setIri("tok", flowToken);
   actionLog.update(pss.asUpdate().toString());
   ```

3. **Remove split documentation** — CODE_STYLE.md "In-memory vs Fuseki"
   section and R21 "raw StringBuilder is correct for in-memory" caveat
   are no longer needed. One code path for both backends.

4. **Re-run full test suite** against all three backends:
   - `tmemory` (default)
   - `fuseki-embedded` (mvn test -Dengine.dataset.type=fuseki-embedded)
   - Standalone Fuseki (docker compose up fuseki + mvn test -Dengine.dataset.type=fuseki)

## Scope

Engine-only change. No methodology, no stage contracts, no quality-gate
scripts. Concepts and syncs are unchanged — only the completion write
path in the base classes.

## Status

Deferred from v0.1.1. The split-brain approach is correct and tested for
the current Jena version. This upgrade removes the split by aligning the
parser versions.

## Experiment findings (2026-08-08)

All attempts to use `<< >>` RDF-star syntax in SPARQL UPDATE templates
failed against Jena 6.1.0's in-memory parser. This is NOT a bug — it's
intentional W3C SPARQL 1.2 Update compliance. The in-memory parser no
longer accepts the lenient early-draft syntax that Jena 5.2.0 tolerated.

| Approach | Result |
|---|---|
| `StringBuilder` + `INSERT DATA` + `<< >>` (5.2.0) | Passes |
| `StringBuilder` + `INSERT DATA` + `<< >>` (6.1.0) | Fails — parser rejects |
| `NodeFmtLib.str()` + `INSERT DATA` + `<< >>` (6.1.0) | Fails — same rejection |
| `PSS.asUpdate()` + `INSERT DATA` + `<< >>` (6.1.0) | Fails — string parser rejects |
| `INSERT { } WHERE { }` + `<< >>` (6.1.0) | Fails — same rejection |

**Root cause:** Jena 6.x in-memory UPDATE parser enforces strict W3C SPARQL
1.2 grammar, which does not allow `<< >>` in UPDATE templates at all.
RDF-star quoted triples are only legal in query patterns (SELECT, CONSTRUCT,
ASK). This is the same restriction Fuseki enforces over HTTP. The lenient
Jena 5.2.0 behavior was a backward-compatibility holdover that has been
removed.

**The permanent fix:** bypass the string parser entirely. `UpdateBuilder`
and `ParameterizedSparqlString.asUpdate()` produce `UpdateRequest` objects
that Jena handles natively — no string parsing involved. The fix is
`ActionLog.update(UpdateRequest)` that passes directly to Jena's execution
layer.

**Conclusion:** The issue is NOT a version mismatch — Jena's in-memory parser
is deliberately lenient (backward-compatible with early RDF-star drafts),
while Fuseki strictly enforces the W3C SPARQL 1.2 Update grammar. No version
bump will make the in-memory parser accept `<< >>` in UPDATE templates
again — the stricter behavior is intentional and permanent.

The correct fix is to bypass the SPARQL string parser entirely:
`ActionLog.update(UpdateRequest)` that passes a programmatically-built
`UpdateRequest` object directly to Jena's `UpdateExecutionFactory`.
The `UpdateBuilder` API produces spec-compliant update operations that
work with both in-memory and remote Fuseki.

**Next steps:** add `ActionLog.update(UpdateRequest)` that calls
`UpdateExecutionFactory.create(request).execute(dataset)` directly. Then
migrate `writeReifiedOutcome` to use `UpdateBuilder` with
`NodeFactory.createTripleNode()` and pass the resulting `UpdateRequest`
to the new method.
