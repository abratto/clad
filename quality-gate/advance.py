#!/usr/bin/env python3
"""
advance.py — Gate-driven advance for a CLAD feature.

This is the *only* sanctioned way for an agent to move between stages. Instead
of the agent deciding what comes next (and possibly skipping a stage or its
verification), the agent finishes a stage and runs:

    python3 quality-gate/advance.py --feature features/UC-XX-<slug>

The script owns the transition decision. It:

  1. Determines the stage that just completed (the furthest populated stage,
     or --stage if given).
  2. Runs the sequence / entry guard (verify_stage_sequence.py) so a skipped
     upstream stage or an unapproved upstream gate is caught immediately.
  3. Runs that stage's deterministic cross-stage checks, reusing the existing
     quality-gate/verify_*.py scripts. Checks whose inputs are not present yet
     are reported as `skip`, not failure.
  4. Writes a tamper-evident receipt (.gate-receipt.json) into the stage's
     output directory.
  5. Emits the next instruction:
       - PASS + no gate      -> the next stage's CONTEXT path + a ready prompt.
       - PASS + human gate    -> the gate summary + a STOP-for-approval prompt.
       - FAIL                 -> the specific defects + a correction prompt.

The agent must treat this script's stdout as its next instruction and must not
open another stage's CONTEXT.md on its own initiative.

Exit codes:
  0   — advanced to the next stage (or the feature is complete)
  1   — the stage has defects; do not advance
  10  — the stage passed but a human gate approval is required; do not advance
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

import clad_stages as cs
from verify_stage_sequence import compute_output_hash, gate_approved, gate_status

HERE = os.path.dirname(os.path.abspath(__file__))
BAR = "=" * 64
AGENT_INSTRUCTION = "  >>> Agent instruction:"
RESUME_FILE = "RESUME.md"

AUTONOMY_LEVELS = ("gated", "auto", "yolo")


def read_clad_property(feature_root: str, key: str) -> str | None:
    """Find clad.properties by walking up from the feature root and return the
    value for `key`, or None."""
    d = os.path.abspath(feature_root)
    while True:
        candidate = os.path.join(d, "clad.properties")
        if os.path.isfile(candidate):
            with open(candidate) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    if k.strip() == key:
                        return v.strip()
            return None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def resolve_autonomy(feature_root: str, cli_value: str | None) -> str:
    """Precedence: --autonomy flag > CLAD_AUTONOMY env > clad.properties >
    default 'gated'. The agent must not set this itself; it comes from the
    human via config or an explicit in-conversation instruction."""
    value = (cli_value
             or os.environ.get("CLAD_AUTONOMY")
             or read_clad_property(feature_root, "workflow.autonomy")
             or "gated").strip().lower()
    if value not in AUTONOMY_LEVELS:
        print(f"WARN  unknown workflow.autonomy '{value}', falling back to 'gated'")
        value = "gated"
    return value


def set_gate_status(feature_root: str, gate: int, status: str) -> bool:
    """Write a gate status token into RESUME.md. Returns True if a matching
    gate line was found and updated."""
    resume_path = os.path.join(feature_root, RESUME_FILE)
    if not os.path.isfile(resume_path):
        return False
    with open(resume_path) as fh:
        text = fh.read()
    label = cs.GATE_LABELS[gate]
    pattern = rf"(- \*\*Gate {gate} \({re.escape(label)}\):\*\*)\s+`[\w-]+`.*"
    new_text, n = re.subn(pattern, rf"\1 `{status}`", text, count=1)
    if n:
        with open(resume_path, "w") as fh:
            fh.write(new_text)
    return bool(n)


def run_script(script: str, argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, os.path.join(HERE, script), *argv],
        capture_output=True, text=True)


def git_sha(feature_root: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=feature_root, capture_output=True, text=True)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def determine_stage(feature_root: str, explicit: str | None):
    if explicit:
        stage = cs.stage_by_id(explicit)
        if stage is None:
            print(f"FAIL  unknown stage id: {explicit}")
            sys.exit(1)
        return stage
    last = -1
    for i, stage in enumerate(cs.STAGES):
        if cs.dir_is_populated(stage.output_dir(feature_root)):
            last = i
    if last < 0:
        print(BAR)
        print("  ADVANCE — no stage output found yet.")
        print("  Start at Stage 01 — open:")
        print(f"    {cs.relpath(cs.STAGES[0].context_path(feature_root))}")
        print(BAR)
        sys.exit(0)
    return cs.STAGES[last]


def run_checks(feature_root: str, stage: cs.Stage) -> list[dict]:
    results = []
    for check in stage.checks:
        missing = [p for p in check.requires(feature_root)
                   if not (os.path.exists(p) and (
                       os.path.isfile(p) and os.path.getsize(p) > 0
                       or os.path.isdir(p) and cs.dir_is_populated(p)))]
        if missing:
            results.append({
                "name": check.name, "script": check.script, "status": "skip",
                "detail": "inputs not present: "
                          + ", ".join(cs.relpath(m, feature_root) for m in missing),
                "exit": None,
            })
            continue
        proc = run_script(check.script, check.build_args(feature_root))
        status = "pass" if proc.returncode == 0 else "fail"
        detail = (proc.stdout or "") + (proc.stderr or "")
        results.append({
            "name": check.name, "script": check.script, "status": status,
            "detail": detail.strip(), "exit": proc.returncode,
        })
    return results


def write_receipt(feature_root: str, stage: cs.Stage, results: list[dict],
                  result: str, seq_detail: str, autonomy: str = "gated") -> str:
    out_dir = stage.output_dir(feature_root)
    receipt = {
        "stage": stage.id,
        "stage_label": stage.label,
        "feature": os.path.basename(feature_root.rstrip("/")),
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_sha": git_sha(feature_root),
        "autonomy": autonomy,
        "output_hash": compute_output_hash(out_dir),
        "sequence_guard": seq_detail,
        "checks": [
            {k: v for k, v in r.items() if k != "detail"} for r in results
        ],
        "result": result,
    }
    path = os.path.join(out_dir, ".gate-receipt.json")
    with open(path, "w") as fh:
        json.dump(receipt, fh, indent=2)
        fh.write("\n")
    return path


def set_resume_field(text: str, label: str, value: str) -> str:
    pattern = rf"^(- \*\*{re.escape(label)}:\*\*).*$"
    replacement = rf"\1 `{value}`"
    new_text, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    return new_text if n else text


def update_resume(feature_root: str, completed: cs.Stage,
                  nxt: cs.Stage | None) -> None:
    resume_path = os.path.join(feature_root, RESUME_FILE)
    if not os.path.isfile(resume_path):
        return
    with open(resume_path) as fh:
        text = fh.read()
    text = set_resume_field(text, "Last completed stage",
                            f"Stage {completed.id} — {completed.label}")
    if nxt is not None:
        text = set_resume_field(text, "Current stage",
                                f"Stage {nxt.id} — {nxt.label}")
        text = set_resume_field(text, "Next stage",
                                f"Stage {nxt.id} — {nxt.label}")
        text = set_resume_field(
            text, "Next file to open",
            cs.relpath(nxt.context_path(feature_root), feature_root))
    else:
        text = set_resume_field(text, "Current stage", "None — feature complete")
        text = set_resume_field(text, "Next stage", "None — feature complete")
    with open(resume_path, "w") as fh:
        fh.write(text)


# --------------------------------------------------------------------------
# Output blocks
# --------------------------------------------------------------------------

def print_check_summary(results: list[dict]) -> None:
    if not results:
        print("  Checks run: (none deterministic at this stage)")
        return
    print("  Checks run:")
    for r in results:
        marker = {"pass": "pass", "fail": "FAIL", "skip": "skip"}[r["status"]]
        print(f"    [{marker}] {r['name']}")
        if r["status"] == "skip":
            print(f"           {r['detail']}")


def print_failures(results: list[dict]) -> None:
    for r in results:
        if r["status"] != "fail":
            continue
        print(f"\n  --- {r['name']} ({r['script']}) ---")
        for line in (r["detail"] or "").splitlines()[:20]:
            print(f"    {line}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gate-driven advance for a CLAD feature")
    parser.add_argument("--feature", required=True,
                        help="Feature root path (e.g. features/UC-XX-<slug>)")
    parser.add_argument("--stage", default=None,
                        help="Stage id that just completed (default: infer)")
    parser.add_argument("--autonomy", default=None, choices=AUTONOMY_LEVELS,
                        help="Override workflow.autonomy for this run only "
                             "(gated | auto | yolo). Normally set in "
                             "clad.properties by the human, not here.")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    if not os.path.isdir(feature_root):
        print(f"FAIL  feature root not found: {feature_root}")
        sys.exit(1)

    stage = determine_stage(feature_root, args.stage)
    feature_name = os.path.basename(feature_root.rstrip("/"))
    autonomy = resolve_autonomy(feature_root, args.autonomy)

    if autonomy != "gated":
        print(BAR)
        print(f"  !!! AUTONOMY = {autonomy.upper()} — reduced human oversight !!!")
        if autonomy == "auto":
            print("  Human gates will be AUTO-APPROVED. Checks still block.")
        else:
            print("  Human gates AUTO-APPROVED and check failures are WARNINGS.")
            print("  Only a fully skipped stage (artefact-chain gap) still stops.")
        print(BAR)

    # --- 1. Sequence / entry guard -----------------------------------------
    seq = run_script("verify_stage_sequence.py",
                     ["--feature", feature_root, "--through", stage.id])
    seq_out = (seq.stdout or "") + (seq.stderr or "")
    if seq.returncode != 0:
        print(BAR)
        print(f"  ADVANCE BLOCKED — sequence integrity failure at Stage "
              f"{stage.id} ({stage.label})")
        print(f"  Feature: {feature_name}")
        print(BAR)
        for line in seq_out.strip().splitlines():
            print(f"  {line}")
        print()
        print(AGENT_INSTRUCTION)
        print("  A stage was skipped or an upstream human gate is not approved.")
        print("  Return to the earliest failing stage above and complete it in")
        print("  order. Do NOT advance. Re-run this command afterwards.")
        print("  (This is a structural integrity stop and is enforced even under")
        print("  autonomy=yolo — an entire stage's artefacts are missing.)")
        print(BAR)
        write_receipt(feature_root, stage, [], "fail", seq_out.strip(), autonomy)
        sys.exit(1)

    # --- 2. Stage checks ----------------------------------------------------
    results = run_checks(feature_root, stage)
    failed = [r for r in results if r["status"] == "fail"]

    if failed and autonomy != "yolo":
        write_receipt(feature_root, stage, results, "fail", seq_out.strip(),
                      autonomy)
        print(BAR)
        print(f"  ADVANCE BLOCKED — Stage {stage.id} ({stage.label}) has defects")
        print(f"  Feature: {feature_name}")
        print(BAR)
        print_check_summary(results)
        print_failures(results)
        print()
        print(AGENT_INSTRUCTION)
        print(f"  Re-run Stage {stage.id} to fix the failures above.")
        print(f"  Open: {cs.relpath(stage.context_path(feature_root), feature_root)}")
        print("  Do NOT advance to the next stage. Re-run this command after fixing.")
        print(BAR)
        sys.exit(1)

    result_label = "pass"
    if failed:  # autonomy == "yolo": downgrade to a non-blocking warning
        result_label = "pass-with-warnings"
    receipt_path = write_receipt(feature_root, stage, results, result_label,
                                 seq_out.strip(), autonomy)
    if failed:
        print(BAR)
        print(f"  WARN (yolo) — Stage {stage.id} ({stage.label}) has "
              f"{len(failed)} failing check(s), advancing anyway:")
        print_failures(results)
        print(BAR)

    # --- 3. Human gate boundary --------------------------------------------
    if stage.gate_after is not None:
        gate = stage.gate_after
        resume_path = os.path.join(feature_root, RESUME_FILE)
        resume_text = ""
        if os.path.isfile(resume_path):
            with open(resume_path) as fh:
                resume_text = fh.read()
        if not gate_approved(resume_text, gate):
            if autonomy in ("auto", "yolo"):
                wrote = set_gate_status(feature_root, gate, "auto-approved")
                print(BAR)
                print(f"  Stage {stage.id} PASSED. HUMAN GATE {gate} "
                      f"({cs.GATE_LABELS[gate]}) AUTO-APPROVED (autonomy={autonomy}).")
                if not wrote:
                    print("  NOTE: no gate line found in RESUME.md to record this.")
                print("  A human did NOT review these artefacts. Recorded as")
                print("  `auto-approved` in RESUME.md for later inspection.")
                print(BAR)
            else:
                present = run_script("present_gate.py",
                                     ["--feature", feature_root, "--gate", str(gate)])
                print(BAR)
                print(f"  Stage {stage.id} ({stage.label}) PASSED its checks.")
                print(f"  This is HUMAN GATE {gate} ({cs.GATE_LABELS[gate]}). STOP.")
                print(BAR)
                print_check_summary(results)
                print(f"  Receipt: {cs.relpath(receipt_path, feature_root)}")
                print()
                print(present.stdout.rstrip())
                print()
                print(AGENT_INSTRUCTION)
                print("  Present the artefact summary above to the human and WAIT.")
                print("  Do NOT advance. When the human explicitly says 'approved', run:")
                print(f"    python3 quality-gate/approve_gate.py --feature {args.feature} --gate {gate}")
                print("  then re-run:")
                print(f"    python3 quality-gate/advance.py --feature {args.feature}")
                print(BAR)
                sys.exit(10)

    # --- 4. Advance ---------------------------------------------------------
    nxt = cs.next_stage(stage.id)
    update_resume(feature_root, stage, nxt)

    print(BAR)
    print(f"  ADVANCE — Stage {stage.id} ({stage.label}) PASSED")
    print(f"  Feature: {feature_name}")
    print(BAR)
    print_check_summary(results)
    print(f"  Receipt: {cs.relpath(receipt_path, feature_root)}")
    print()
    if nxt is None:
        print("  This was the final stage. The feature pipeline is complete.")
        print("  Run Stage 05 closure checks and prepare the gate commit.")
        print(BAR)
        sys.exit(0)

    print(f"  NEXT STAGE: {nxt.id} — {nxt.label}")
    print("  Open this contract and execute it:")
    print(f"    {cs.relpath(nxt.context_path(feature_root), feature_root)}")
    print()
    print(AGENT_INSTRUCTION)
    print("  Load the CONTEXT.md above, load only the files its Inputs table")
    print("  names, and produce its Outputs. Do NOT open any other stage.")
    print("  When finished, run:")
    print(f"    python3 quality-gate/advance.py --feature {args.feature}")
    print(BAR)
    sys.exit(0)


if __name__ == "__main__":
    main()
