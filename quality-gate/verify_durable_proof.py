#!/usr/bin/env python3
"""
verify_durable_proof.py — a persistent profile must record a passing durable
(Postgres) run before the feature closes.

Why this exists (experiment finding 19):
  The durable persistence lane (`-Dclad.postgres=true`) is Docker-gated and is
  NOT in `test.command`, so the 04e/05 mechanical gates pass while a real
  Postgres-only defect (an unquoted DEFAULT, a NOT NULL column) sits undetected —
  and the feature is called closed green. A profile that declares
  `storage.persistent=true` is asserting durability matters, so its Stage-05
  close must carry evidence that the durable lane actually ran and passed.

Contract:
  When `storage.persistent` is true, `stages/05_verify/output/durable-proof.md`
  must exist with:
    - a `- **Command:** ` line naming the durable invocation (must contain
      `clad.postgres` or `durable`), and
    - a `- **Result:** ` line whose value is `PASS`.
  A non-persistent profile SKIPs (nothing to prove).

Usage:
  python3 verify_durable_proof.py --feature features/UC-XX-<slug>

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402


def _property(feature_root, key):
    """Read a property from the nearest clad.properties (walk up)."""
    probe = os.path.abspath(feature_root)
    while True:
        cfg = os.path.join(probe, "clad.properties")
        if os.path.isfile(cfg):
            with open(cfg, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    stripped = line.strip()
                    if stripped.startswith("#") or "=" not in stripped:
                        continue
                    k, v = stripped.split("=", 1)
                    if k.strip() == key:
                        return v.strip()
            return ""
        parent = os.path.dirname(probe)
        if parent == probe:
            return ""
        probe = parent


def _field(text, label):
    match = re.search(rf"^-\s*\*\*{re.escape(label)}:\*\*\s*`?([^`\n]+)`?",
                      text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--feature", required=True)

    def body(args: argparse.Namespace) -> cr.Verdict:
        feature_root = os.path.abspath(args.feature)
        persistent = (_property(feature_root, "storage.persistent") or "").lower()
        if persistent not in ("true", "1", "yes", "on"):
            return cr.Verdict.skip(
                "not a persistent profile — no durable proof required")

        path = os.path.join(feature_root, "stages", "05_verify", "output",
                            "durable-proof.md")
        if not os.path.isfile(path):
            return cr.Verdict.fail(
                "persistent profile closed without durable proof",
                [cr.Problem(
                    f"missing {os.path.relpath(path)} — run the durable lane "
                    f"(e.g. `mvn test -Dclad.postgres=true`) and record its "
                    f"command and result (finding 19)", bullet=True)])

        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        problems = []
        command = _field(text, "Command")
        result = _field(text, "Result")
        if not command or not re.search(r"clad\.postgres|durable", command):
            problems.append(
                "`- **Command:**` must name the durable invocation "
                "(e.g. `mvn test -Dclad.postgres=true`)")
        if result.upper() != "PASS":
            problems.append(
                f"`- **Result:**` must be `PASS`, got `{result or 'unset'}`")
        if problems:
            return cr.Verdict.fail(
                "durable proof is incomplete", [cr.Problem(p, bullet=True) for p in problems])
        return cr.Verdict.ok("durable lane recorded as passing")

    return cr.run_check(
        "A persistent profile records a passing durable run at close",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
