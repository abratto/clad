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
from verify_stage_sequence import active_reentry_change, stage_has_evidence

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
    reentry_change = active_reentry_change(feature_root)
    if reentry_change:
        reentry_stage, change_path = reentry_change
        current = cs.stage_by_id(reentry_stage)
        changed_after = os.path.getmtime(change_path)
        last_child = cs.stage_index("04e-green")
        for stage in cs.STAGES[cs.stage_index(reentry_stage):last_child + 1]:
            output = stage.output_dir(feature_root)
            if not cs.dir_is_populated(output):
                continue
            newest_evidence = max(
                os.path.getmtime(os.path.join(root, name))
                for root, _dirs, files in os.walk(output)
                for name in files
                if not name.startswith(".")
            )
            if newest_evidence >= changed_after:
                current = stage
        return current
    last = None
    for stage in cs.STAGES:
        if stage_has_evidence(feature_root, stage.id):
            last = stage
    return last


def main():
    print(f"{BAR}")
    print("  CLAD artefact pipeline gate")
    print(f"{BAR}")

    all_pass = True
    any_features = False

    # Maintenance changes are governed independently of UC stage output.
    code, out, err = run_script(
        "verify_maintenance_change_readiness.py", ["--base", "HEAD"])
    detail = (out + err).strip()
    if code != 0:
        all_pass = False
        print("\n  [FAIL] maintenance_change_readiness")
        for line in detail.splitlines()[:6]:
            print(f"        {line}")
    elif "no engine" not in detail:
        print("\n  [PASS] maintenance_change_readiness")

    # Documentation cross-reference integrity (feature-independent).
    code, out, err = run_script("verify_links.py", [])
    detail = (out + err).strip()
    ok = code == 0
    mark = "PASS" if ok else "FAIL"
    print(f"\n  [{mark}] doc_links")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail.strip():
        print(f"        {detail.splitlines()[0]}")

    # Cross-feature shared-concept contract drift (feature-independent).
    code, out, err = run_script("verify_shared_action_contracts.py",
                                ["--features-dir", str(REPO_ROOT / "features")])
    detail = (out + err).strip()
    ok = code == 0
    mark = "PASS" if ok else "FAIL"
    print(f"\n  [{mark}] shared_action_contracts")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail.strip():
        for line in detail.splitlines():
            print(f"        {line}")

    # Project-level concept registry (feature-independent).
    code, out, err = run_script("verify_concept_registry.py",
                                ["--features-dir", str(REPO_ROOT / "features")])
    detail = (out + err).strip()
    ok = code == 0
    mark = "PASS" if ok else "FAIL"
    print(f"\n  [{mark}] concept_registry")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail.strip():
        for line in detail.splitlines():
            print(f"        {line}")

    # Every non-bootstrap sync pins its flow root (feature-independent): a flow
    # token scopes a match to one flow, but within a flow any matching rule
    # fires, so two use cases sharing a completion fire each other's rules.
    code, out, err = run_script("verify_sync_flow_pin.py",
                                ["--features-dir", str(REPO_ROOT / "features")])
    detail = (out + err).strip()
    ok = code == 0
    mark = "PASS" if ok else "FAIL"
    print(f"\n  [{mark}] sync_flow_pin")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail.strip():
        for line in detail.splitlines():
            print(f"        {line}")

    # The canonical concept corpus is current and self-consistent
    # (feature-independent): every Gate-2-approved proposal is on the canonical
    # entry's promotion history, and the companions agree with it.
    code, out, err = run_script("verify_concept_corpus_current.py",
                                ["--features-dir", str(REPO_ROOT / "features")])
    detail = (out + err).strip()
    ok = code == 0
    mark = "PASS" if ok else "FAIL"
    print(f"\n  [{mark}] concept_corpus_current")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail.strip():
        for line in detail.splitlines():
            print(f"        {line}")

    # Governance records do not go stale (advisory, project-level): a finished
    # change whose record was never `closed` is invisible to the readiness
    # guards until the next change trips over it.
    code, out, err = run_script("verify_governance_hygiene.py",
                                ["--features-dir", str(REPO_ROOT / "features"),
                                 "--maintenance-dir", str(REPO_ROOT / "maintenance")])
    detail = (out + err).strip()
    mark = "WARN" if detail.startswith("WARN") else "PASS"
    print(f"\n  [{mark}] governance_hygiene")
    if detail:
        for line in detail.splitlines()[:10]:
            print(f"        {line}")

    # A mechanism claim cites the code it rests on (the flow-pin record's wrong
    # explanation would have been caught by its citation). Blocking for active
    # platform records and the load-bearing SYNCHRONIZATIONS sections.
    code, out, err = run_script("verify_mechanism_citations.py",
                                ["--maintenance-dir", str(REPO_ROOT / "maintenance"),
                                 "--sync-doc", str(REPO_ROOT / "methodology/architecture/SYNCHRONIZATIONS.md")])
    detail = (out + err).strip()
    ok = code == 0
    print(f"\n  [{'PASS' if ok else 'FAIL'}] mechanism_citations")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail and not detail.startswith("PASS"):
        for line in detail.splitlines()[:4]:
            print(f"        {line}")

    # Backticked code references resolve (advisory): a rename must not leave a
    # citation pointing at nothing.
    code, out, err = run_script("verify_code_refs.py",
                                ["--dirs", "methodology", "maintenance", "templates"])
    detail = (out + err).strip()
    mark = "WARN" if detail.startswith("WARN") else "PASS"
    print(f"\n  [{mark}] code_refs")
    if detail:
        for line in detail.splitlines()[:8]:
            print(f"        {line}")

    # The cross-UC shared-trigger view is current (feature-independent): it is
    # the only surface for a duplicate trigger across use cases, and it went
    # stale once because nothing checked it.
    code, out, err = run_script("verify_shared_triggers_current.py",
                                ["--features-dir", str(REPO_ROOT / "features")])
    detail = (out + err).strip()
    ok = code == 0
    mark = "PASS" if ok else "FAIL"
    print(f"\n  [{mark}] shared_triggers_current")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail.strip():
        for line in detail.splitlines():
            print(f"        {line}")

    # Sync `then` carries the authored result, not the transport frame
    # (feature-independent).
    code, out, err = run_script("verify_sync_then_shape.py",
                                ["--features-dir", str(REPO_ROOT / "features")])
    detail = (out + err).strip()
    ok = code == 0
    mark = "PASS" if ok else "FAIL"
    print(f"\n  [{mark}] sync_then_shape")
    if not ok:
        all_pass = False
        for line in detail.splitlines()[:8]:
            print(f"        {line}")
    elif detail.strip():
        for line in detail.splitlines():
            print(f"        {line}")

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

        # --- 1b. Profile-path integrity (skips silently when the feature
        # declares no _config/package-and-layout.md) ---
        code, out, err = run_script(
            "verify_profile_paths.py",
            ["--feature", root],
        )
        detail = (out + err).strip()
        ok = code == 0
        if not ok or "WARN" in detail:
            mark = "PASS" if ok else "FAIL"
            print(f"    [{mark}] profile paths")
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
