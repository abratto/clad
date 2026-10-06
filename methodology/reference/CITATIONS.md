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
`?_eachthen` in `where` clauses. Two controlled divergences are
documented in [`../architecture/CONCEPTS.md`](../architecture/CONCEPTS.md)
(multiplicity annotations, qualified operational principles).

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
operational principles is a deliberate gap in CLAD: gate review and the
frozen Acceptance Spec plus mutation-gated unit tests
([`../../docs/decisions/0001-spec-driven-testing.md`](../../docs/decisions/0001-spec-driven-testing.md))
are the practical substitutes. Full Alloy verification
remains appropriate if state-machine bugs become the dominant failure
category in a given project.

This notation was first applied in full in `abratto/tastetag` before
being formalised here.

## Why concepts aren't objects

Daniel Jackson. **Why concepts aren't objects.** *The Essence of Software*
(blog), December 2025.

- URL: [essenceofsoftware.com/posts/concepts-and-oop](https://essenceofsoftware.com/posts/concepts-and-oop/)

This essay is the source for CLAD's concept-naming guidance. A concept is
chunked around a **purpose** — a capability named by a gerund or noun phrase
(`Posting`, `PasswordAuthentication`, `Upvoting`) — not around an **entity**
(`Post`, `User`, `Comment`). The entity is a separate *individual* type that
appears in the concept's `## State` section as the set the concept ranges
over. It also supplies the "separating views" argument (naming vs
authentication vs profiling) and the object-oriented "bad smells" that
`verify_concept_state_relational.py` turns into a deterministic Stage 02 gate.

## Axiomatic Design — the FR×DP matrix

Nam P. Suh. **Axiomatic Design: Advances and Applications.** Oxford
University Press, 2001.

Axiomatic Design contributes the review instrument behind Stage 03's
`verify_concept_matrix.py` (maintenance change `ad-design-deepening`):
use-case scenarios are the **functional requirements (FRs)** and concepts
are the **design parameters (DPs)**. Suh's Independence Axiom — maintain
the independence of the functional requirements — becomes inspectable as a
sparse, near-diagonal FR×DP matrix: a solid column is a God Object, two
identical columns are redundant DPs, and heavily shared rows are boundary
confusion. The checker realises it mechanically; the verdict (when to
split, merge, or re-examine a boundary) stays a human modelling judgement,
which is why the check runs advisively at Stage 03.

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

## Spec-driven testing in agent loops

Birgitta Böckeler. **TDD inside the agent loop — theater or actual
value?** *Exploring Gen AI* (martinfowler.com), 2026.

- URL: [martinfowler.com/articles/exploring-gen-ai/tdd-in-the-agent-loop.html](https://martinfowler.com/articles/exploring-gen-ai/tdd-in-the-agent-loop.html)

This article (and the WebApp1K, TDAD, and TGen work it draws on) is the
source of CLAD's move away from in-loop TDD ceremony toward spec-driven
verification. It supports the two decisions recorded in
[`docs/decisions/0001-spec-driven-testing.md`](../../docs/decisions/0001-spec-driven-testing.md):
tests are most useful to an agent as frozen, human-approved acceptance
expectations and as regression/effectiveness sensors, not as a
design-discovery process; and test effectiveness is monitored by
outcome (mutation score) rather than by mandating a red-green process.
The article's "Approved Scenarios" pattern is the model for CLAD's
frozen Acceptance Spec. `methodology/implementation/TESTING.md` is the
adaptation; it is a paraphrase, not a derivative copy.

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

Alan Potosnak. **Tastetag** (private project, 2025–2026).

This starter distils prose, examples, and the Java reference
implementation (the Jena profile is retired) that originated in the Tastetag
project. The
Alloy-style notation used in concept specs was first developed and
battle-tested there before being formalised in this starter. The
starter is re-licensed under Apache-2.0 with the author's
permission.

## How to cite this starter

```
Potosnak, A. (2026). CLAD — Contract-Led, Artefact-Driven Development.
GitHub: https://github.com/abratto/clad
```
