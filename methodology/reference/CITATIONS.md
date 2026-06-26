# Citations and attributions

The CLAD starter integrates ideas from several external works. All are
cited here; all are also acknowledged in the repository-root
[`NOTICE`](../../NOTICE) file.

## Legible architecture / WYSIWID pattern

Eagon Meng and Daniel Jackson. **What You See Is What It Does: A
Structural Pattern for Legible Software.** In *Proceedings of the 2025
ACM SIGPLAN International Symposium on New Ideas, New Paradigms, and
Reflections on Programming and Software (Onward! 2025)*, part of SPLASH.

- DOI: [10.1145/3759429.3762628](https://doi.org/10.1145/3759429.3762628)
- arXiv: [2508.14511](https://arxiv.org/abs/2508.14511)
- License of the paper: CC BY-NC 4.0

The paper introduces concepts as polymorphic, independent units with
state, actions, and an operational principle; synchronizations as
declarative coordination rules; and a bootstrap `Web` concept that
owns the HTTP surface. It also discusses provenance via flow tokens
and an RDF/SPARQL action log. The summaries in
[`../architecture/`](../architecture/) are paraphrases of these ideas;
they are not derivative copies of the paper's prose. Implementations
that follow the WYSIWID pattern should cite the paper.

**Notation alignment.** CLAD's concept and synchronization specification
languages are aligned with the paper's Sections 4–5 syntax: paper-style
state notation (`field: SubjectType -> FieldType`), `concept <Name>
[TypeParams]` header with `purpose` section, `sync <Name>` header with
`when { }` / `where { }` / `then { }` block syntax, `Concept/action:`
namespace qualifiers, `?variable` binding, and `bind()` / `OPTIONAL` /
`?_eachthen` in `where` clauses. Three controlled divergences are
documented in [`../architecture/CONCEPTS.md`](../architecture/CONCEPTS.md)
(multiplicity annotations, qualified operational principles) and
[`../architecture/WEB_CONCEPT.md`](../architecture/WEB_CONCEPT.md)
(Web entry action is `handle` not `request`).

## Alloy — relational state and operational principle notation

Daniel Jackson. **Software Abstractions: Logic, Language, and Analysis.**
MIT Press, 2006; revised edition 2012.

- MIT Press: [mitpress.mit.edu/9780262528900](https://mitpress.mit.edu/9780262528900)

CLAD adopts Alloy's relational notation for the `## State` section of
concept specs:

```
relation(subject: Type) -> field: Type   -- multiplicity
```

and the `after`/`then` trace form for the `## Operational Principle`
section. Neither the Alloy language syntax nor the Alloy Analyzer tool
is required — the notation is used for precision and human readability
only. The paper's use of Alloy `check` for mechanical verification of
operational principles is a deliberate gap in CLAD: gate review and
red-first TDD are the practical substitutes. Full Alloy verification
remains appropriate if state-machine bugs become the dominant failure
category in a given project.

This notation was first applied in full in `abratto/tastetag` before
being formalised here.

## Interpretable Context Methodology (ICM)

Jake Van Clief. **Interpretable Context Methodology (ICM).** 2026.

- arXiv: [2603.16021](https://arxiv.org/abs/2603.16021)
- Repository: [github.com/RinDig/Interpretable-Context-Methodology-ICM-](https://github.com/RinDig/Interpretable-Context-Methodology-ICM-)
- License: MIT

ICM contributes the five-layer context hierarchy, the numbered-stage
workspace pattern, and the `CONTEXT.md` stage-contract format
(`Inputs`, `Process`, `Outputs`). The CLAD scaffold under `features/`
and the templates in `templates/stage-CONTEXT.md` are direct
adaptations of these ideas.

## ORM / Conceptual Schema Design Procedure

Mustafa Jarrar. **Object Role Modelling (ORM/ORM-ML) and the
Conceptual Schema Design Procedure (CSDP).** Cited in CLAD as the
source of the seven-step drafting procedure summarised in
[`../architecture/DATA_MODEL_NOTES.md`](../architecture/DATA_MODEL_NOTES.md).

- Personal page: [jarrar.info](https://www.jarrar.info)
- Representative paper: Jarrar, M. *Towards Methodological Principles
  for Ontology Engineering*, PhD thesis, Vrije Universiteit Brussel,
  2005, and subsequent ORM/ORM-ML papers.

CLAD borrows the shape of the CSDP and adapts it to per-concept data
models under hard rule R2 (one named region per concept). The full
ORM-ML notation is **not** adopted; readers who want the notation
should consult Jarrar's papers directly.

## Source of the CLAD reference implementation

Alan Potosnak. **abratto/tastetag** —
[github.com/abratto/tastetag](https://github.com/abratto/tastetag).

This starter distils prose, examples, and the Java/Micronaut/Jena
reference implementation that originated in `tastetag/methodology/`.
The Alloy-style notation used in concept specs was first developed and
battle-tested in `tastetag` before being formalised in this starter.
The starter is re-licensed under Apache-2.0 with the author's
permission.

## How to cite this starter

```
Potosnak, A. (2026). CLAD — Contract-Led, Artefact-Driven Development.
GitHub: https://github.com/abratto/clad
```
