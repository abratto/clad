---
name: clad-quality-gate
description: Run CLAD quality-gate verification scripts between stages. Use when self-auditing stage outputs against cross-stage consistency rules, file manifests, scenario coverage, contract parity, and derivation compliance.
---

# CLAD Quality Gate

> **Role:** aggregator for the self-audit scripts between stages. The
> stage `CONTEXT.md` `## Verify` section is authoritative for the exact
> commands; this skill is the pointer, not a script list.

## What this skill covers

Self-audit discipline: running the verification scripts between stages
to catch defects before human gates. Scripts check file manifests, scenario
coverage, outcome alignment, action chains, sync matrices, data models,
contract parity, Gherkin presence, Gherkin derivation, and concept test
derivation.

## Where to look

Do not work from a hand-copied script list — it drifts. Use the sources, in
this order:

1. **The current stage's `CONTEXT.md` `## Verify` section** — the authoritative
   commands for *this* stage. Run every item.
2. **[`quality-gate/INDEX.md`](../../quality-gate/INDEX.md)** — the generated,
   always-current map of every gate script: what it checks, when it runs
   (stage / project-level / pre-commit), and whether it is a gate or advisory.
   Regenerate with `python3 quality-gate/generate_gate_index.py`.
3. **The one-shot check** — an aggregator that runs every applicable check for
   every feature in one invocation:

   ```
   python3 quality-gate/verify_artefacts.py
   ```

   This is the same gate `test.command` runs before the profile tests. Prefer it
   at the end of every stage for a single-pass check (`./clad verify` is the
   same thing).

## Process

1. Run every `Verify` item in the current stage's `CONTEXT.md`.
2. If any script fails, stop and surface the defect.
3. Do not advance until all checks pass.

## Hard constraints

- Scripts are deterministic — a failing script is a real defect.
- Do not skip verification scripts between stages.
- Fix the earliest upstream stage that owns the defect, not the current output.
