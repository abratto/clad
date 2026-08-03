#!/usr/bin/env python3
"""
verify_stage_sequence.py — Generalised entry / sequence guard for a CLAD
feature.

Why this exists:
  The per-feature workflow is an ordered pipeline (01 -> 01a -> 01b -> ...).
  `verify_gate_approval.py` guards the three *human* gate transitions. This
  script generalises that idea to *every* transition: it makes skipping a
  stage a hard, detectable error rather than something only a human might
  notice in review.

It checks three invariants for a feature:

  1. No gap. The set of populated stage output directories must be a
     contiguous prefix of the canonical order. A populated stage with an
     empty predecessor means a stage was skipped.

  2. Gates honoured. For every human gate whose stage lies before the
     furthest populated stage, the corresponding gate must be marked
     `approved` in the feature's RESUME.md (same check as
     verify_gate_approval.py).

  3. Receipts current (optional, --require-receipts). Every populated stage
     up to the target must carry a `.gate-receipt.json` whose recorded
     output hash matches the current output contents. A stale or missing
     receipt means the stage's checks were not (re)run after its last edit.

Usage:
  python3 verify_stage_sequence.py --feature features/UC-XX-<slug>
  python3 verify_stage_sequence.py --feature features/UC-XX-<slug> --through 03b
  python3 verify_stage_sequence.py --feature features/UC-XX-<slug> --require-receipts

Exit codes:
  0  — sequence intact through the target stage
  1  — a gap, an unapproved required gate, or a stale/missing receipt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

import clad_stages as cs

# A gate counts as cleared for sequencing if a human approved it or if the
# configured autonomy level auto-approved it. The distinction is preserved in
# the RESUME.md text so a reviewer can see which gates a human never inspected;
# stricter checks (e.g. verify_gate_approval.py) may still require a literal
# human `approved`.
APPROVED_STATES = {"approved", "auto-approved"}
LEGACY_PARENT_EVIDENCE = {
    "04d": ("concept-tdd.md", "concept-test-derivation.md"),
    "04e": ("sync-tdd.md", "sync-test-derivation.md"),
}


def _field_value(text: str, label: str) -> str:
    match = re.search(
        rf"^[-*]?\s*\*\*{re.escape(label)}:\*\*\s*`?([^`\n]+)`?\s*$",
        text,
        re.MULTILINE,
    )
    return match.group(1).strip().lower() if match else ""


def active_reentry_change(feature_root: str) -> tuple[str, str] | None:
    """Return the earliest stage and path from one active change record."""
    changes_dir = os.path.join(feature_root, "_changes")
    if not os.path.isdir(changes_dir):
        return None
    active = []
    for name in os.listdir(changes_dir):
        if not name.endswith(".md"):
            continue
        path = os.path.join(changes_dir, name)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        if _field_value(text, "Status") == "active":
            stage_id = _field_value(text, "Earliest re-entry stage")
            if stage_id == "04d":
                stage_id = "04d-red"
            elif stage_id == "04e":
                stage_id = "04e-red"
            if cs.stage_by_id(stage_id) is not None:
                active.append((stage_id, path))
    if len(active) == 1:
        return active[0]
    return None


def active_reentry_stage(feature_root: str) -> str | None:
    """Return the earliest stage from one explicitly active change record."""
    change = active_reentry_change(feature_root)
    return change[0] if change else None


def _legacy_parent_present(feature_root: str, phase: str) -> bool:
    output_dir = os.path.join(
        feature_root, "stages", "04_implement", f"{phase}_{'concept-tdd' if phase == '04d' else 'sync-tdd'}", "output")
    return any(os.path.isfile(os.path.join(output_dir, name))
               for name in LEGACY_PARENT_EVIDENCE[phase])


def _historical_green_summary(feature_root: str, stage_id: str) -> bool:
    stage = cs.stage_by_id(stage_id)
    if stage is None:
        return False
    marker = (
        "CLAD historical-green-summary: includes "
        f"{stage_id.removesuffix('-green')}-red evidence"
    )
    output_dir = stage.output_dir(feature_root)
    for root, _dirs, files in os.walk(output_dir):
        for name in files:
            if name.startswith("."):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    if marker in handle.read():
                        return True
            except OSError:
                continue
    return False


def stage_has_evidence(feature_root: str, stage_id: str) -> bool:
    """Return whether a canonical stage has direct or migration-only evidence."""
    stage = cs.stage_by_id(stage_id)
    if stage is None:
        return False
    if cs.dir_is_populated(stage.output_dir(feature_root)):
        return True
    if active_reentry_stage(feature_root) is not None:
        return False

    phase = stage_id[:3]
    if phase not in LEGACY_PARENT_EVIDENCE:
        return False
    red_id = f"{phase}-red"
    green_id = f"{phase}-green"
    red = cs.stage_by_id(red_id)
    green = cs.stage_by_id(green_id)
    child_outputs_empty = not (
        cs.dir_is_populated(red.output_dir(feature_root))
        or cs.dir_is_populated(green.output_dir(feature_root))
    )
    if child_outputs_empty and _legacy_parent_present(feature_root, phase):
        return True
    return stage_id == red_id and _historical_green_summary(feature_root, green_id)


def gate_status(resume_text: str, gate_num: int) -> str | None:
    """Return the recorded status token for a gate, or None if not found."""
    label = cs.GATE_LABELS.get(gate_num, f"Gate {gate_num}")
    pattern = rf"^- \*\*Gate {gate_num} \({re.escape(label)}\):\*\*\s+`([\w-]+)`"
    m = re.search(pattern, resume_text, re.MULTILINE)
    return m.group(1) if m else None


def gate_approved(resume_text: str, gate_num: int) -> bool:
    """True if the gate is human-approved or auto-approved."""
    return gate_status(resume_text, gate_num) in APPROVED_STATES


def compute_output_hash(out_dir: str) -> str:
    """Stable hash over the non-hidden files in a stage output directory."""
    h = hashlib.sha256()
    files = []
    for root, _dirs, names in os.walk(out_dir):
        for n in sorted(names):
            if n.startswith("."):
                continue
            files.append(os.path.join(root, n))
    for path in sorted(files):
        rel = os.path.relpath(path, out_dir)
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        try:
            with open(path, "rb") as fh:
                h.update(fh.read())
        except OSError:
            pass
        h.update(b"\0")
    return h.hexdigest()


def furthest_populated_index(feature_root: str) -> int:
    """Index of the last stage (in canonical order) with a populated output
    directory, or -1 if none."""
    last = -1
    for i, stage in enumerate(cs.STAGES):
        if cs.dir_is_populated(stage.output_dir(feature_root)):
            last = i
    return last


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify CLAD stage sequence integrity for a feature")
    parser.add_argument("--feature", required=True,
                        help="Feature root path (e.g. features/UC-XX-<slug>)")
    parser.add_argument("--through", default=None,
                        help="Stage id to check up to (default: furthest populated)")
    parser.add_argument("--require-receipts", action="store_true",
                        help="Also require a current .gate-receipt.json per stage")
    parser.add_argument("--no-gates", action="store_true",
                        help="Skip the human-gate approval checks")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    if not os.path.isdir(feature_root):
        print(f"FAIL  feature root not found: {feature_root}")
        sys.exit(1)

    if args.through:
        target = cs.stage_index(args.through)
        if target < 0:
            print(f"FAIL  unknown stage id: {args.through}")
            sys.exit(1)
    else:
        target = furthest_populated_index(feature_root)
        if target < 0:
            print("PASS  no stages populated yet — nothing to sequence-check")
            sys.exit(0)

    resume_path = os.path.join(feature_root, "RESUME.md")
    resume_text = ""
    if os.path.isfile(resume_path):
        with open(resume_path) as fh:
            resume_text = fh.read()

    ok = True

    # Invariant 1 — no gap (contiguous prefix).
    for i in range(target + 1):
        stage = cs.STAGES[i]
        out_dir = stage.output_dir(feature_root)
        if not stage_has_evidence(feature_root, stage.id):
            print(f"FAIL  Stage {stage.id} ({stage.label}) output is empty, "
                  f"but a later stage is populated — a stage was skipped.")
            print(f"       expected artefacts in: {cs.relpath(out_dir, feature_root)}")
            ok = False

    # Invariant 2 — gates honoured for gate stages strictly before target.
    if not args.no_gates:
        for i in range(target):
            stage = cs.STAGES[i]
            if stage.gate_after is None:
                continue
            status = gate_status(resume_text, stage.gate_after)
            label = cs.GATE_LABELS[stage.gate_after]
            if status not in APPROVED_STATES:
                found = status or "missing"
                print(f"FAIL  Gate {stage.gate_after} ({label}) after Stage "
                      f"{stage.id} is '{found}', but work advanced past it. "
                      f"Human approval is required before Stage "
                      f"{cs.STAGES[i + 1].id}.")
                ok = False

    # Invariant 3 — receipts current (optional).
    if args.require_receipts:
        for i in range(target + 1):
            stage = cs.STAGES[i]
            out_dir = stage.output_dir(feature_root)
            if not cs.dir_is_populated(out_dir):
                continue
            receipt_path = os.path.join(out_dir, ".gate-receipt.json")
            if not os.path.isfile(receipt_path):
                print(f"FAIL  Stage {stage.id} ({stage.label}) has no "
                      f".gate-receipt.json — its checks were never recorded.")
                ok = False
                continue
            try:
                with open(receipt_path) as fh:
                    receipt = json.load(fh)
            except (OSError, json.JSONDecodeError):
                print(f"FAIL  Stage {stage.id} receipt is unreadable: {receipt_path}")
                ok = False
                continue
            if receipt.get("result") != "pass":
                print(f"FAIL  Stage {stage.id} receipt records result="
                      f"'{receipt.get('result')}', not 'pass'.")
                ok = False
                continue
            current = compute_output_hash(out_dir)
            if receipt.get("output_hash") != current:
                print(f"FAIL  Stage {stage.id} receipt is stale — output changed "
                      f"since it was recorded. Re-run advance.py for this stage.")
                ok = False

    if ok:
        print(f"PASS  sequence intact through Stage {cs.STAGES[target].id} "
              f"({cs.STAGES[target].label})")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
