#!/usr/bin/env python3
"""
generate_gate_index.py — emit `quality-gate/INDEX.md` from the machine map.

Why this exists:
  `quality-gate/` is a flat directory of ~69 Python files. The hand-written
  catalogs (skills/clad-quality-gate/SKILL.md, QUALITY_GATE.md) restate what
  `clad_stages.py` already knows, so they drift. This generator reads the real
  map — `clad_stages.STAGES` (stage -> checks), plus the project-level calls in
  `verify_artefacts.py`, the pre-commit hook, and `test.command` — and emits one
  navigable index. A consistency test (`test_gate_index.py`) keeps it current.

Usage:
  python3 quality-gate/generate_gate_index.py           # write INDEX.md
  python3 quality-gate/generate_gate_index.py --check    # exit 1 if stale
"""

import argparse
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clad_stages as cs  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
INDEX_PATH = os.path.join(HERE, "INDEX.md")

# Scripts that are not stage checks but run as part of the pipeline.
PROJECT_LEVEL = [
    ("verify_artefacts.py", "the one-shot artefact pipeline gate (runs the stage checks for every feature + the project-level checks below)"),
    ("verify_links.py", "relative markdown cross-reference links resolve"),
    ("verify_shared_action_contracts.py", "a concept action/outcome vocabulary shared across features does not drift"),
    ("verify_concept_registry.py", "one introducer per concept; no redefinition; promotion completeness"),
    ("verify_sync_flow_pin.py", "every non-bootstrap sync names its flow root last"),
    ("verify_concept_corpus_current.py", "the canonical corpus is not behind its promotions"),
    ("verify_governance_hygiene.py", "no stale governance records (advisory)"),
    ("verify_mechanism_citations.py", "a mechanism claim cites the code it rests on"),
    ("verify_code_refs.py", "backticked code references resolve (advisory)"),
    ("verify_reference_integrity.py", "no dangling artefact reference after a rename"),
    ("verify_shared_triggers_current.py", "the generated cross-UC shared-trigger view is current"),
    ("verify_sync_then_shape.py", "a sync `then` carries the authored result, not a transport frame"),
]

PRE_COMMIT = [
    ("verify_stage_sequence.py", "no stage was skipped; cleared gates recorded in RESUME.md"),
    ("verify_iterative_change_coupling.py", "implementation changes carry their matching Stage 02/03 artefacts"),
    ("verify_maintenance_change_readiness.py", "engine/profile/config changes have a governed maintenance record"),
]

ADVISORY = {
    "verify_code_refs.py", "verify_governance_hygiene.py", "verify_concept_matrix.py",
    "verify_shared_triggers_current.py", "verify_close_evidence.py", "verify_sync_cycle_graph.py",
    "verify_sync_overlap.py", "verify_collection_coverage.py",
}


def _summary(script):
    """The script's one-line purpose: its module docstring's first sentence."""
    path = os.path.join(HERE, script)
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    doc = ast.get_docstring(tree) or ""
    text = " ".join(line.strip() for line in doc.splitlines() if line.strip())
    text = re.sub(r"^verify_\w+\.py\s*[—-]\s*", "", text)
    # First sentence only.
    match = re.match(r"(.+?\.)\s", text + " ")
    return (match.group(1) if match else text).strip()


def _read_test_command():
    path = os.path.join(REPO_ROOT, "clad.properties")
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("test.command"):
                return line.split("=", 1)[1].strip()
    return ""


def collect():
    """Return {script: {'when': [...], 'summary': str, 'advisory': bool, 'why': str}}."""
    entries = {}

    def add(script, when, *, advisory=None):
        e = entries.setdefault(script, {"when": [], "summary": _summary(script),
                                        "advisory": script in ADVISORY, "why": ""})
        if when and when not in e["when"]:
            e["when"].append(when)
        if advisory is not None:
            e["advisory"] = advisory

    for stage in cs.STAGES:
        for check in stage.checks:
            when = f"stage {stage.id} ({stage.label})"
            if check.skip_in_artefact_gate:
                when += " — run by the profile test command"
            add(check.script, when, advisory=False)

    for script, why in PROJECT_LEVEL:
        add(script, "project-level (every `verify_artefacts` run)")
        entries[script]["why"] = why

    for script, why in PRE_COMMIT:
        add(script, "pre-commit hook")
        entries[script]["why"] = why

    # Any verify_ script not reached above is hand-run tooling (e.g. the
    # advisory analysis scripts) — list it, but do not claim a stage.
    for script in sorted(os.listdir(HERE)):
        if script.startswith("verify_") and script.endswith(".py") \
                and script not in entries:
            add(script, "by hand (advisory tooling)")

    return entries


def render():
    entries = collect()
    test_cmd = _read_test_command()
    lines = []
    lines.append("<!-- GENERATED by quality-gate/generate_gate_index.py — do not edit by hand. -->")
    lines.append("")
    lines.append("# quality-gate script index")
    lines.append("")
    lines.append("The generated map of the `quality-gate/` scripts. `clad_stages.py` is the")
    lines.append("machine source of truth for stage order and the stage→checks map; this file is")
    lines.append("its readable projection, kept current by `quality-gate/tests/test_gate_index.py`.")
    lines.append("")
    lines.append("- **One-shot check:** `python3 quality-gate/verify_artefacts.py` (the same gate `test.command` runs).")
    lines.append("- **Per-stage authoritative commands:** each stage's `CONTEXT.md` §Verify.")
    lines.append(f"- **`test.command`:** `{test_cmd}`")
    lines.append("")
    lines.append("`gate` = blocking; `advisory` = prints WARNs but exits 0.")
    lines.append("")
    lines.append("| Script | What it checks | When it runs | Kind |")
    lines.append("|---|---|---|---|")
    for script in sorted(entries):
        e = entries[script]
        summary = e.get("why") or e["summary"] or "—"
        when = "; ".join(e["when"]) or "—"
        kind = "advisory" if e["advisory"] else "gate"
        lines.append(f"| `{script}` | {summary} | {when} | {kind} |")
    lines.append("")
    lines.append("## Non-`verify_` helper scripts")
    lines.append("")
    lines.append("- **Orchestration:** `clad_stages.py` (stage map), `advance.py` (gate-driven advance),")
    lines.append("  `present_gate.py`, `approve_gate.py`, `approve_maintenance_change.py`, `promote_concepts.py`.")
    lines.append("- **Generators:** `generate_syncs.py`, `generate_syncs_java.py`, `generate_contract.py`,")
    lines.append("  `generate_data_model.py`, `generate_concepts_catalog.py`, `generate_shared_triggers.py`,")
    lines.append("  `generate_sync_cards.py`, `generate_feature_files.py`, `rename_sync.py`, `generate_gate_index.py`.")
    lines.append("- **Shared parsers:** `artifact_parsers.py` (the artefact-grammar single source of truth),")
    lines.append("  `descriptor.py`, `describe_feature.py` (the machine contract — see `MACHINE_CONTRACT.md`).")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate/verify quality-gate/INDEX.md")
    parser.add_argument("--check", action="store_true",
                        help="Exit 1 if INDEX.md is stale (write nothing)")
    args = parser.parse_args()

    content = render()
    if args.check:
        current = ""
        if os.path.isfile(INDEX_PATH):
            with open(INDEX_PATH, encoding="utf-8") as fh:
                current = fh.read()
        if current != content:
            print("FAIL  quality-gate/INDEX.md is stale — "
                  "run: python3 quality-gate/generate_gate_index.py")
            return 1
        print("PASS  quality-gate/INDEX.md is current")
        return 0

    with open(INDEX_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"WROTE {os.path.relpath(INDEX_PATH, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
