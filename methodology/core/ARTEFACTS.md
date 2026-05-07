# Artefacts

An **artefact** is a file on disk produced by following a contract. It is
the trail behind the work; the contract is the trail ahead of it.

## Categories

| Category | Examples | Lives in |
|---|---|---|
| **Spec artefacts** | `usecase.md`, `*.concept.md`, `*.sync.md` | `features/UC-XX/stages/NN_*/output/` |
| **Code artefacts** | Source files, build configs | `reference-impl/` |
| **Trace artefacts** | Flow-token logs, verification traces | `features/UC-XX/stages/05_verify/output/` |
| **Workspace artefacts** | `CONTEXT.md` files, reference material | `methodology/`, `templates/`, `_config/` |

## Properties

Every artefact must be:

1. **Readable as plain text.** Markdown, YAML, JSON, source code. No
   binary formats for primary artefacts. (Generated binaries are fine
   as long as the source is plain text.)
2. **Diffable.** If you cannot see what changed in a PR, the artefact
   is not granular enough.
3. **Owned by one stage.** Stage `02_concepts/` owns concept specs.
   Stage `03_syncs/` owns sync specs. No artefact is co-owned.
4. **Reachable from a contract.** You should always be able to point at
   an artefact and say which contract authorised it.

## Stage outputs as intermediate representations

Each stage's `output/` folder behaves like an **intermediate
representation** in a multi-pass compiler:

- It is the complete, sufficient input to the next stage.
- It can be inspected on its own without re-running the previous stage.
- Editing it is the supported way for the human to influence what
  happens next.

This is what makes the discipline reversible: a bad stage 3 output is
fixed by re-running stage 3 with edited inputs, not by patching the
final code.

## Output edits as diagnostic signal

When a human edits a stage's output, two things happen:

1. The edit takes effect immediately for the rest of the pipeline.
2. The edit is information about a possible source-level defect.

If the same kind of edit appears two or three runs in a row, that is a
signal: the stage's `CONTEXT.md`, a reference file, or a template
needs to change so the agent does not produce the regrettable output
again. See `core/CLAD.md` §P5.
