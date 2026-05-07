# Citations and attributions

The CLAD starter integrates ideas from two external works. Both are
cited here; both are also acknowledged in the repository-root
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
[`../architecture/ORM_NOTES.md`](../architecture/ORM_NOTES.md).

- Personal page: [jarrar.info](https://www.jarrar.info)
- Representative paper: Jarrar, M. *Towards Methodological Principles
  for Ontology Engineering*, PhD thesis, Vrije Universiteit Brussel,
  2005, and subsequent ORM/ORM-ML papers.

CLAD borrows the *shape* of the seven-step CSDP and adapts it to
per-concept schemas under hard rule R2 (one named region per
concept). The full ORM-ML notation is **not** adopted; readers who
want the notation should consult Jarrar's papers directly.

## Source of the CLAD reference implementation

Alan Potosnak. **abratto/tastetag** —
[github.com/abratto/tastetag](https://github.com/abratto/tastetag).

This starter distils prose, examples, and the Java/Micronaut/Jena
reference implementation that originated in `tastetag/methodology/`.
The starter is re-licensed under Apache-2.0 with the author's
permission.

## How to cite this starter

```
Potosnak, A. (2026). CLAD — Contract-Led, Artefact-Driven Development.
GitHub: https://github.com/abratto/clad
```
