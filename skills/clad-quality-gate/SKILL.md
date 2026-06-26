---
name: clad-quality-gate
description: Run CLAD quality-gate verification scripts between stages. Use when self-auditing stage outputs against cross-stage consistency rules, file manifests, scenario coverage, SPEC parity, and derivation compliance.
---

# CLAD Quality Gate

## What this skill covers

Self-audit discipline: running the 10 verification scripts between stages
to catch defects before human gates. Scripts check file manifests, scenario
coverage, outcome alignment, action chains, sync matrices, data models,
SPEC parity, Gherkin presence, Gherkin derivation, and concept test
derivation.

## Quick reference

Load these files:

1. `methodology/implementation/QUALITY_GATE.md` — pre-commit quality
   gate rationale and checklist
2. The stage `CONTEXT.md` for the specific `Verify` commands to run

## Scripts

All scripts live in `quality-gate/` at the repo root and are run
with `python3`:

| Script | Checks |
|---|---|
| `verify_file_manifest.py` | `output/` contains exactly expected files |
| `verify_scenario_coverage.py` | goal→scenario→chain→sync coverage |
| `verify_outcome_alignment.py` | chain-table outcomes match SPEC enums |
| `verify_action_chain.py` | action name consistency across artefacts |
| `verify_sync_matrix.py` | every sync has complete Sync Contract Matrix |
| `verify_data_model.py` | CSDP structure compliance |
| `verify_spec_parity.py` | action parity between concepts and SPECs |
| `verify_feature_file_presence.py` | `.feature` file exists |
| `verify_gherkin_derivation.py` | `.feature` derivation rules compliance |
| `verify_concept_test_derivation.py` | SPEC outcome→test coverage |

## Process

1. Run every `Verify` item in the current stage's `CONTEXT.md`.
2. If any script fails, stop and surface the defect.
3. Do not advance until all checks pass.

## Hard constraints

- Scripts are deterministic — a failing script is a real defect.
- Do not skip verification scripts between stages.
- Fix the earliest upstream stage that owns the defect, not the current output.
