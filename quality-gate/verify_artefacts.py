#!/usr/bin/env python3
"""
verify_artefacts.py — Pre-test CLAD artefact pipeline gate.

Auto-discovers all UC-* feature directories, determines each one's current
stage (furthest populated output/), and runs:
  1. The stage-sequence guard (no skipped stages, gates honoured).
  2. The per-stage deterministic checks wired in clad_stages.py.

Checks flagged with skip_in_artefact_gate (e.g. cucumber_green, which runs
the actual test framework) are excluded — those are handled by the profile's
test command that follows this script.

Wire this into clad.properties as the first half of test.command:
    test.command=python3 quality-gate/verify_artefacts.py && mvn test

Exit: 0 = all artefact checks passed; 1 = one or more failed.
"""

import os
import subprocess
import sys
from pathlib import Path

import clad_stages as cs

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent

BAR = "=" * 60


def run_script(script_name, args):
    proc = subprocess.run(
        [sys.executable, str(HERE / script_name)] + list(args),
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr


def discover_features():
    features_dir = REPO_ROOT / "features"
    if not features_dir.is_dir():
        return
    for d in sorted(features_dir.iterdir()):
        if d.is_dir() and d.name.startswith("UC-"):
            yield d.name, str(d)


def _current_stage(feature_root):
    last = None
    for stage in cs.STAGES:
        if cs.dir_is_populated(stage.output_dir(feature_root)):
            last = stage
    return last


def main():
    print(f"{BAR}")
    print("  CLAD artefact pipeline gate")
    print(f"{BAR}")

    all_pass = True
    any_features = False

    for name, root in discover_features():
        any_features = True
        stage = _current_stage(root)

        if stage is None:
            print(f"\n  {name}: no populated stages — skipping")
            continue

        print(f"\n  {name}  Stage {stage.id} — {stage.label}")

        # --- 1. Sequence guard (always) ---
        code, out, err = run_script(
            "verify_stage_sequence.py",
            ["--feature", root, "--through", stage.id],
        )
        detail = (out + err).strip()
        ok = code == 0
        mark = "PASS" if ok else "FAIL"
        print(f"    [{mark}] stage sequence")
        if not ok:
            all_pass = False
            for line in detail.splitlines()[:6]:
                print(f"          {line}")

        # --- 2. Per-stage checks ---
        checks = [c for c in stage.checks if not c.skip_in_artefact_gate]

        if not checks:
            print("    Checks: (none deterministic at this stage)")

        for check in checks:
            missing = [
                p for p in check.requires(root)
                if not (
                    os.path.exists(p)
                    and (
                        os.path.isfile(p) and os.path.getsize(p) > 0
                        or os.path.isdir(p) and cs.dir_is_populated(p)
                    )
                )
            ]
            if missing:
                print(f"    [SKIP] {check.name} — inputs not present yet")
                continue

            code, out, err = run_script(check.script, check.build_args(root))
            detail = (out + err).strip()
            ok = code == 0
            mark = "PASS" if ok else "FAIL"
            print(f"    [{mark}] {check.name}")
            if not ok:
                all_pass = False
                for line in detail.splitlines()[:6]:
                    print(f"          {line}")

        # --- 3. Iterative-change readiness (cross-cutting) ---
        code, out, err = run_script(
            "verify_iterative_change_readiness.py",
            ["--feature", root, "--base", "HEAD"],
        )
        detail = (out + err).strip()
        ok = code == 0
        if ok and "no iterative" in detail:
            # No iterative changes in scope — don't clutter output
            pass
        else:
            mark = "PASS" if ok else "FAIL"
            print(f"    [{mark}] iterative_change_readiness")
            if not ok:
                all_pass = False
                for line in detail.splitlines()[:6]:
                    print(f"          {line}")

    if not any_features:
        print("\n  No UC-* features found — nothing to check.")

    print(f"\n{BAR}")
    if all_pass:
        print("  RESULT: artefact pipeline intact — proceeding to tests")
        print(f"{BAR}")
        sys.exit(0)
    else:
        print("  RESULT: artefact defects found — fix before running tests")
        print("  (see FAIL lines above)")
        print(f"{BAR}")
        sys.exit(1)


if __name__ == "__main__":
    main()
