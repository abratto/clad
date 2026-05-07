# features/

This folder holds **use cases**. One folder per use case, named
`UC-XX-short-name`. Inside each use case, work is organised by **stage**
under `stages/NN_*/`, following the ICM scaffold described in
[`../methodology/implementation/STAGES.md`](../methodology/implementation/STAGES.md).

A use case folder looks like:

```
UC-XX-name/
├── README.md          What the use case is, where it stands
├── _config/           Feature-scoped reference (Layer 3)
└── stages/
    ├── 01_usecase/
    ├── 02_concepts/
    ├── 03_syncs/
    ├── 04_implement/
    └── 05_verify/
```

The numbered stages run in order. Each has a `CONTEXT.md` (the stage's
contract) and an `output/` (the artefacts produced). The human reviews
between stages.

## Worked example

[`UC-00-login/`](UC-00-login/) is a small, illustrative example: a
classic username/password login. It is intentionally simple so that
nothing is hidden behind incidental complexity. Use it as a template
for your own first feature.
