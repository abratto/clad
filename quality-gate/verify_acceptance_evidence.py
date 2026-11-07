#!/usr/bin/env python3
"""
verify_acceptance_evidence.py — Stage 05: the running app produced the approved
Acceptance-Spec behaviour, not just a test that predicts it.

Why this exists:
  The Acceptance Spec (Gate 3) states each scenario's expected token chain and
  response; the native flow tests assert them in code; `trace.md` records a
  runtime chain the author assembles. None of those proves the *running app*
  produced the approved chain/status/body per scenario. This check reads the
  evidence a test run emitted (`acceptance-evidence.json`, assembled by
  `capture_observations.py`) and compares it to the spec.

Evidence: `stages/05_verify/output/acceptance-evidence.json`, shape

    { "<scenario>": { "runtime": [...], "status": 200, "body": {...},
                       "readback": {...}  # persistent profile } }

Missing evidence:
  * a legacy feature (a `verification-trace.md`, the pre-rename trace) is
    grandfathered (SKIP) — evidence is forward-only;
  * otherwise it is a FAIL: a Stage-05 close must carry produced evidence.

Usage:
  python3 verify_acceptance_evidence.py --feature-root features/UC-XX [--evidence PATH]

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acceptance_evidence as ae  # noqa: E402
import check_runner as cr  # noqa: E402


def _property(feature_root, key):
    probe = os.path.abspath(feature_root)
    while True:
        cfg = os.path.join(probe, "clad.properties")
        if os.path.isfile(cfg):
            with open(cfg, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    s = line.strip()
                    if s.startswith("#") or "=" not in s:
                        continue
                    k, v = s.split("=", 1)
                    if k.strip() == key:
                        return v.strip()
            return ""
        parent = os.path.dirname(probe)
        if parent == probe:
            return ""
        probe = parent


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--feature-root", required=True)
        parser.add_argument("--evidence", default="",
                            help="Evidence JSON (default: "
                                 "05_verify/output/acceptance-evidence.json)")

    def body(args: argparse.Namespace) -> cr.Verdict:
        feature = os.path.abspath(args.feature_root)
        spec_path = os.path.join(feature, "stages", "04_implement",
                                 "04c_acceptance-tests", "output",
                                 "acceptance-spec.md")
        if not os.path.isfile(spec_path):
            return cr.Verdict.skip("no Acceptance Spec (04c not reached)")
        evidence_path = args.evidence or os.path.join(
            feature, "stages", "05_verify", "output",
            "acceptance-evidence.json")
        if not os.path.isfile(evidence_path):
            legacy = os.path.join(feature, "stages", "05_verify", "output",
                                  "verification-trace.md")
            if os.path.isfile(legacy):
                return cr.Verdict.skip(
                    "legacy feature (pre-evidence `verification-trace.md`) — "
                    "acceptance evidence is forward-only")
            return cr.Verdict.fail(
                "no acceptance evidence recorded",
                [cr.Problem(
                    f"missing {os.path.relpath(evidence_path)} — run the flow "
                    f"tests, then assemble evidence with "
                    f"`capture_observations.py --flows-dir <dir> --out "
                    f"{os.path.relpath(evidence_path)}`", bullet=True)])

        spec = ae.parse_acceptance_spec(spec_path)
        evidence = ae.load_evidence(evidence_path)
        persistent = (_property(feature, "storage.persistent") or "").lower() in (
            "true", "1", "yes", "on")
        problems = ae.compare(spec, evidence, persistent=persistent)
        if problems:
            return cr.Verdict.fail(
                "runtime evidence does not match the Acceptance Spec",
                [cr.Problem(p, bullet=True) for p in problems])
        return cr.Verdict.ok(
            f"{len(spec)} scenario(s) match their Acceptance-Spec runtime evidence")

    return cr.run_check(
        "Runtime evidence matches the frozen Acceptance Spec", body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
