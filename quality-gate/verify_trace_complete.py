#!/usr/bin/env python3
"""Blocking Stage 05 check: the canonical trace carries real evidence.

The trace generator emits `<TODO: …>` markers. Passing Stage 05 while they
remain would make the closure artefact a promise rather than evidence.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--feature-root", required=True)

    def body(args: argparse.Namespace) -> cr.Verdict:
        feature = os.path.abspath(args.feature_root)
        trace = os.path.join(feature, "stages", "05_verify", "output", "trace.md")
        legacy = os.path.join(feature, "stages", "05_verify", "output",
                              "verification-trace.md")
        if not os.path.isfile(trace):
            if os.path.isfile(legacy):
                return cr.Verdict.ok(
                    "legacy trace name accepted; rename to trace.md when "
                    "regenerating this feature")
            return cr.Verdict.fail(f"missing {trace}")

        text = open(trace, encoding="utf-8", errors="replace").read()
        todos = [line.strip() for line in text.splitlines() if "<TODO:" in line]
        if todos:
            verdict = cr.Verdict.fail(
                "trace still contains unresolved evidence markers:",
                [cr.Problem(line) for line in todos[:10]])
            verdict.detail = ("      replace them with captured runtime evidence "
                              "before closing.")
            return verdict
        if not text.lstrip().startswith("Resume point:"):
            return cr.Verdict.fail(
                "trace.md must begin with a `Resume point:` line")

        failures = []
        # Check both top-level scenarios (`##`) and their per-branch sub-cases
        # (`###`); a sub-case's runtime chain is evidence too.
        for section in re.split(r"^(?=#{2,3}\s)", text, flags=re.MULTILINE)[1:]:
            name = section.splitlines()[0].strip()
            expected_block = re.search(
                r"\*\*Expected chain[^\n]*:\*\*\n(.*?)(?=\n- \*\*|\Z)",
                section, re.DOTALL)
            runtime_line = re.search(r"\*\*Runtime trace:\*\*(.*)", section)
            if not expected_block or not runtime_line:
                continue
            expected = re.findall(r"`([^`]+)`", expected_block.group(1))
            runtime = re.findall(r"`([^`]+)`", runtime_line.group(1))
            if expected and runtime and expected != runtime:
                failures.append(cr.Problem(
                    "runtime chain does not match the approved chain",
                    where=name,
                    fix=f"expected: {' -> '.join(expected)}; "
                        f"observed: {' -> '.join(runtime)}"))
        if failures:
            return cr.Verdict.fail(
                "trace runtime chains diverge from the chain tables:", failures)

        return cr.Verdict.ok("Stage 05 trace carries resolved runtime evidence")

    return cr.run_check("Verify Stage 05 trace evidence", body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
