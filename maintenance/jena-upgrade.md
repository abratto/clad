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
