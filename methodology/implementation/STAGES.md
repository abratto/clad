# Stages — how the CLAD loop maps onto the ICM scaffold

CLAD's contract loop has five steps:

```
use case  ->  concepts  ->  syncs  ->  implementation  ->  verification
```

Each step is one ICM stage. A feature is a folder under `features/`
containing a numbered subfolder per stage:

```
features/UC-XX-name/
├── README.md
├── _config/                     Feature-scoped reference (Layer 3)
└── stages/
    ├── 01_usecase/
    │   ├── CONTEXT.md           Stage contract
    │   └── output/              Working artefacts (Layer 4)
    ├── 02_concepts/
    │   ├── CONTEXT.md
    │   ├── references/          Stage-scoped reference
    │   └── output/
    ├── 03_syncs/
    │   ├── CONTEXT.md
    │   └── output/
    ├── 04_implement/
    │   ├── CONTEXT.md
    │   └── output/
    └── 05_verify/
        ├── CONTEXT.md
        └── output/
```

## The stage contract

Each stage's `CONTEXT.md` follows a standard shape. See
[`../../templates/stage-CONTEXT.md`](../../templates/stage-CONTEXT.md):

```
## Inputs
- Layer 4 (working):   ../<previous-stage>/output/
- Layer 3 (reference): ../../../../methodology/architecture/CONCEPTS.md
- Layer 3 (reference): ../../_config/<...>

## Process
<one paragraph saying what the agent does in this stage>

## Outputs
- <file> -> output/

## Verify
- <how the next stage will check this stage's work>
```

The `Inputs` table is **load-bearing**: an agent must load *exactly*
those files, no more. The `Outputs` list is closed: an agent must not
write files that are not on it.

## Stage-by-stage

### Stage 1 — `01_usecase/`

**Input:** the human's request.

**Process:** draft `usecase.md` with: a one-paragraph operational
principle for the *feature* (not for any single concept), the actors,
and the named scenarios the feature must satisfy. Each scenario is a
trigger + expected outcomes.

**Output:** `usecase.md`.

**Gate:** the human edits the use case before stage 2.

### Stage 2 — `02_concepts/`

**Input:** `01_usecase/output/usecase.md`,
`methodology/architecture/CONCEPTS.md`, `templates/concept.md`.

**Process:** identify the concepts the feature requires (one capability
each). For each, draft a `<Name>.concept.md` per the template. Each
must have state, actions, and an operational principle.

**Output:** one `<Name>.concept.md` per concept.

**Gate:** the human reviews concept boundaries — this is the most
common place to catch over-fused or under-split concepts.

### Stage 3 — `03_syncs/`

**Input:** `02_concepts/output/`, the use case (for the `Cites`
section), `methodology/architecture/SYNCHRONIZATIONS.md`,
`templates/sync.md`.

**Process:** for each scenario in the use case, identify the chain of
concept actions that fulfil it. Each link in the chain becomes a sync.

**Output:** one `<name>.sync.md` per coordination rule.

**Gate:** the human checks that every scenario in the use case is
covered by syncs and that no sync contains imperative branching.

### Stage 4 — `04_implement/`

**Input:** `02_concepts/output/`, `03_syncs/output/`,
`methodology/implementation/RULES.md`, the language profile chosen for
the feature.

**Process:** generate or update code under `reference-impl/<profile>/`
that realises the concepts and syncs. Honour all hard rules.

**Output:** code files (under `reference-impl/`) and an
`implementation-manifest.md` in `output/` listing what was generated
and where.

**Gate:** the human runs the build/tests; CI runs the rule checks
(R1–R5 are mechanically detectable in most languages).

### Stage 5 — `05_verify/`

**Input:** the use case, the sync specs, and the running flow-token
log from a representative test execution.

**Process:** for each named scenario, walk the flow-token tree and
check that it matches the chain of syncs and concepts the specs say
it should. Flag any tokens not authorised by a spec.

**Output:** `trace.md` (per-scenario walk) and, if anything failed,
`findings.md` listing the violations.

**Gate:** any finding sends the loop back to whichever stage owns the
defect — typically stage 1 (incomplete use case) or stage 4
(implementation drift).

## Why numbered folders

The numbering is execution order, full stop. Renumbering a folder is
how you change the order. There is no orchestration code to edit. This
is the ICM principle: the filesystem *is* the orchestrator.
