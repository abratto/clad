# Maintenance change — `gate-index`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `quality-gate` documentation (no engine/profile/runtime change)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Generate `quality-gate/INDEX.md` from the machine source of truth (`clad_stages.py` + `verify_artefacts.py`), with a consistency test so it cannot drift; rewrite `skills/clad-quality-gate/SKILL.md` to stop enumerating scripts; add an INDEX pointer atop the `QUALITY_GATE.md` checks table.

## Why

`quality-gate/` is a flat directory of ~69 Python files (51 `verify_*`). The
two hand-written catalogs have drifted because they restate what
`clad_stages.py` already knows:

- `skills/clad-quality-gate/SKILL.md` lists **10** of the 47+ `verify_*`
  scripts;
- `QUALITY_GATE.md` was missing `verify_test_naming` (closed in the earlier
  audit, but the pattern — a hand-copied map — is the defect).

`clad_stages.py` is the real map (stage → checks); `verify_artefacts.py` holds
the project-level and pre-commit calls. Readable generated output makes the
flat directory navigable without moving files (≈125 references hardcode
`quality-gate/verify_*.py` paths, so a reorg is out of scope).

## Rule

1. Add `quality-gate/generate_gate_index.py` that walks `clad_stages.STAGES`
   (stage → checks) plus `verify_artefacts.py`'s project-level calls, the
   pre-commit hook, and `test.command`, and emits `quality-gate/INDEX.md`: one
   row per script — **name · what it checks · when it runs · gate/advisory ·
   run-by-hand/orchestrated**.
2. Add `quality-gate/tests/test_gate_index.py` asserting `INDEX.md` is current
   (regenerate and compare), so it cannot drift.
3. Rewrite `skills/clad-quality-gate/SKILL.md` to point at the stage
   `CONTEXT.md` `## Verify` (authoritative per-stage), `INDEX.md` (the full
   map), and `verify_artefacts.py` (the one-shot check) — stop enumerating.
4. Add a pointer line atop the `QUALITY_GATE.md` checks table to `INDEX.md`.

## Mechanism

`generate_gate_index.collect` reads `clad_stages.STAGES` (stage → checks) plus
the hard-coded project-level/pre-commit lists
(quality-gate/generate_gate_index.py:86) and `render`
(quality-gate/generate_gate_index.py:123) emits the table; `main --check`
(quality-gate/generate_gate_index.py:163) exits 1 when `quality-gate/INDEX.md`
differs from the rendered text, which is what `test_gate_index.py` asserts.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Docs + a generator; no artefact/runtime change |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | no | — |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Gate scripts | yes | new `generate_gate_index.py`; `INDEX.md` (generated) |
| Gate tests | yes | new `test_gate_index.py` |
| Methodology docs | yes | `skills/clad-quality-gate/SKILL.md`, `QUALITY_GATE.md` pointer |
| UC artefact chain | no | — |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| INDEX.md is current (regenerating produces no diff) | unit | `test_gate_index.py::…test_index_is_current`, `…test_index_regeneration_is_deterministic` | pass | — |
| Every wired `verify_*` script appears in INDEX.md | unit | `test_gate_index.py::…test_every_wired_script_listed` | pass | — |
| The skill no longer enumerates scripts | unit | `test_gate_index.py::…test_skill_points_at_the_sources_not_an_enumeration` | pass | — |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 254 passed |

## Gates

### Design gate

To be approved before implementation. Approve with
`./clad approve-maintenance gate-index design`.

### Evidence gate

Cleared: INDEX.md is generated current (its regeneration is a no-op, asserted by the consistency test); every wired script is listed; the skill points at the stage contracts + INDEX.md + verify_artefacts.py and no longer enumerates a partial table; the artefact pipeline is intact (0 WARNs) and the gate suite is green at 254.

## Notes

- No scripts move: the generated index gives clarity without the ~125-reference
  churn.
