# Stage 04 — Implement

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../02_concepts/output/` | 4 | Concept specs |
| `../03_syncs/output/` | 4 | Sync specs |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules (all) |
| `../../../../reference-impl/<profile>/README.md` | 3 | Profile conventions |

## Process

Generate or update code under `reference-impl/<profile>/` that realises
the concepts and syncs. One package (or module) per concept. One
declaration per sync. The HTTP surface lives only in `Web`. Every action
emits a flow token. No concept imports another.

When the work is done, write a small `implementation-manifest.md` here
in `output/` listing the files generated and the commit they landed in.

## Outputs

- `output/implementation-manifest.md` — what landed where

## Verify

- `git grep` shows no cross-concept imports.
- A test exercising `successful-login` produces a flow-token tree
  whose root is `Web.handle POST /login` and whose leaves include
  `Session.open` and `Web.respond`.
- Build and tests pass.

## Status in this seed

This stage's `output/` is intentionally empty in the seed. UC-00-login
is included as a *spec*-level worked example; the implementation
profile under `reference-impl/` is a skeleton. When the
[`reference-impl/java-micronaut-jena/`](../../../../reference-impl/java-micronaut-jena/)
profile is filled in, this stage's output will be populated by the
agent that runs it.
