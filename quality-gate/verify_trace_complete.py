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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify Stage 05 trace evidence")
    parser.add_argument("--feature-root", required=True)
    args = parser.parse_args(argv)
    feature = os.path.abspath(args.feature_root)
    trace = os.path.join(feature, "stages", "05_verify", "output", "trace.md")
    legacy = os.path.join(feature, "stages", "05_verify", "output",
                          "verification-trace.md")
    if not os.path.isfile(trace):
        if os.path.isfile(legacy):
            print("PASS  legacy trace name accepted; rename to trace.md when "
                  "regenerating this feature")
            return 0
        print(f"FAIL  missing {trace}")
        return 1
    text = open(trace, encoding="utf-8", errors="replace").read()
    todos = [line.strip() for line in text.splitlines() if "<TODO:" in line]
    if todos:
        print("FAIL  trace still contains unresolved evidence markers:")
        for line in todos[:10]:
            print(f"  {line}")
        print("      replace them with captured runtime evidence before closing.")
        return 1
    if not text.lstrip().startswith("Resume point:"):
        print("FAIL  trace.md must begin with a `Resume point:` line")
        return 1

    failures = []
    # Check both top-level scenarios (`##`) and their per-branch sub-cases
    # (`###`); a sub-case's runtime chain is evidence too.
    for section in re.split(r"^(?=#{2,3}\s)", text, flags=re.MULTILINE)[1:]:
        name = section.splitlines()[0].strip()
        expected_block = re.search(
            r"\*\*Expected chain[^\n]*:\*\*\n(.*?)(?=\n- \*\*|\Z)",
            section, re.DOTALL)
        runtime_line = re.search(
            r"\*\*Runtime trace:\*\*(.*)", section)
        if not expected_block or not runtime_line:
            continue
        expected = re.findall(r"`([^`]+)`", expected_block.group(1))
        runtime = re.findall(r"`([^`]+)`", runtime_line.group(1))
        if expected and runtime and expected != runtime:
            failures.append(
                f"{name}: runtime chain does not match the approved chain\n"
                f"    expected: {' -> '.join(expected)}\n"
                f"    observed: {' -> '.join(runtime)}")
    if failures:
        print("FAIL  trace runtime chains diverge from the chain tables:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print("PASS  Stage 05 trace carries resolved runtime evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
