# CLAD — Contract-Led, Artefact-Driven Development

> A starter repository for building software with AI coding agents under a
> discipline that keeps every decision **legible, reviewable, and reversible**.

CLAD combines three ideas that, taken together, let a single human reviewer
steer multi-step agent work without losing control of the system being built:

1. **CLAD (process)** — every change flows through *contracts* (small,
   reviewable specs) and produces *artefacts* (files on disk you can diff).
   No work happens off-contract; no artefact is born without a contract.
2. **Legible architecture (WYSIWID pattern)** — runtime is decomposed into
   independent **concepts** (small state machines with explicit operational
   principles) connected only by declarative **synchronizations**. What you
   read in a concept spec is what the running system does. Adapted from
   Meng & Jackson, *What You See Is What It Does* (Onward! 2025).
3. **ICM workspace scaffold** — each feature lives in its own folder of
   numbered stages (`01_usecase/`, `02_concepts/`, …). Each stage has a
   `CONTEXT.md` *contract* (Inputs / Process / Outputs) and an `output/`
   folder the human can inspect and edit before the next stage runs.
   Adapted from Van Clief, *Interpretable Context Methodology*.

```
You write a use case  ->  agent drafts concepts  ->  you edit  ->
agent drafts syncs    ->  you edit  ->  agent implements  ->
agent verifies traces back to the use case.
```

At every arrow there is a folder you can open and a file you can edit.

## Status

**Seed.** This repo bootstraps the methodology, templates, agent guides, a
worked example (`features/UC-00-login/`), and an optional Java reference
profile. The full reference implementation lives at
[abratto/tastetag](https://github.com/abratto/tastetag) and will be ported
into `reference-impl/` over subsequent PRs.

## Quick start

```bash
git clone https://github.com/abratto/clad.git
cd clad
# Read in this order:
#   1. README.md (you are here)
#   2. AGENTS.md             ← canonical guide for any AI coding agent
#   3. methodology/README.md ← reading order for the methodology
#   4. features/UC-00-login/ ← worked example, end to end
```

To start a new feature, copy `features/UC-00-login/` to
`features/UC-XX-your-feature/`, blank the `output/` folders, and rewrite
`stages/01_usecase/output/usecase.md`. Then point your agent at
`features/UC-XX-your-feature/stages/01_usecase/CONTEXT.md`.

## Repository layout

```
clad/
├── README.md
├── LICENSE                          Apache-2.0
├── NOTICE                           Third-party attributions
├── CONTRIBUTING.md
├── AGENTS.md                        Canonical agent guide (single source)
├── CLAUDE.md                        Adapter -> AGENTS.md
├── .github/copilot-instructions.md  Adapter -> AGENTS.md
├── .cursor/rules/clad.mdc           Adapter -> AGENTS.md
├── CONTEXT.md                       Workspace routing (ICM Layer 1)
│
├── methodology/
│   ├── README.md                    Reading order
│   ├── core/                        CLAD: contracts, artefacts, principles
│   ├── architecture/                Legible/WYSIWID: concepts, syncs, flows
│   ├── implementation/              Hard rules + ICM stage mapping
│   └── reference/                   Citations and source pointers
│
├── templates/                       Concept, sync, use-case, flow, stage
│
├── features/
│   ├── README.md
│   └── UC-00-login/                 Worked example
│       ├── README.md
│       ├── _config/                 Feature-scoped reference (Layer 3)
│       └── stages/
│           ├── 01_usecase/
│           ├── 02_concepts/
│           ├── 03_syncs/
│           ├── 04_implement/
│           └── 05_verify/
│
└── reference-impl/
    └── java-micronaut-jena/         Optional Java profile (skeleton)
```

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Citations

- Meng, E. & Jackson, D. (2025). *What You See Is What It Does: A Structural
  Pattern for Legible Software.* Onward! 2025.
  [DOI 10.1145/3759429.3762628](https://doi.org/10.1145/3759429.3762628) ·
  [arXiv 2508.14511](https://arxiv.org/abs/2508.14511)
- Van Clief, J. (2026). *Interpretable Context Methodology (ICM).*
  [arXiv 2603.16021](https://arxiv.org/abs/2603.16021) ·
  [github.com/RinDig/Interpretable-Context-Methodology-ICM-](https://github.com/RinDig/Interpretable-Context-Methodology-ICM-)
