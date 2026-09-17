#!/usr/bin/env python3
"""
verify_sync_then_shape.py — a sync `then` carries the authored result, not the
transport frame.

Why this exists:
  Response framing belongs to the primary adapter, which
  `methodology/overlays/PORTS_AND_ADAPTERS.md` charges with "serialize[ing] it
  to the transport's response". A sync that nests a `body: { … }` into its
  `then` is writing the wire frame into coordination — and it is unenforceable:
  the fluent DSL has no nested-map argument source, and
  `verify_sync_implementation_parity` compares only the `then` *target*, so a
  spec that promises a frame its implementation cannot produce goes unnoticed
  (maintenance change `transport-framing-adapter-owned`).

Rule:
  A `then` argument list is flat — `[ status: 200 ; sessionToken: ?sid ]`. A
  `{ … }` inside a `then` signature is a defect.

Findings: every `Concept/action: [ … { … } … ]` signature line (in the Rule
block or the Sync Contract Matrix) whose argument list contains a brace.

Usage:
  python3 verify_sync_then_shape.py [--features-dir features] [--advisory]

Exit: 0 pass/warn/skip, 1 fail (unless --advisory).
"""

import argparse
import os
import re
import sys

# `Concept/action: [ ... ]` — the argument list stops at the first `]`, so a
# nested `body: { … }` remains inside the captured group.
SIGNATURE = re.compile(r"\b([A-Z]\w*/\w+):\s*\[([^\]]*)\]")


def scan(path):
    """Return a list of (line number, signature) for framed `then` signatures."""
    hits = []
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            for match in SIGNATURE.finditer(line):
                if "{" in match.group(2):
                    hits.append((lineno, match.group(1)))
    return hits


def main():
    parser = argparse.ArgumentParser(
        description="A sync then carries the authored result, not the transport frame")
    parser.add_argument("--features-dir", default="features")
    parser.add_argument("--advisory", action="store_true",
                        help="Report findings as warnings (exit 0)")
    args = parser.parse_args()

    if not os.path.isdir(args.features_dir):
        print(f"SKIP  no features directory at {args.features_dir}")
        return 0

    scanned = 0
    findings = []
    for feature in sorted(os.listdir(args.features_dir)):
        if not feature.startswith("UC-"):
            continue
        sync_dir = os.path.join(args.features_dir, feature, "stages", "03_syncs",
                                "output")
        if not os.path.isdir(sync_dir):
            continue
        for name in sorted(os.listdir(sync_dir)):
            if not name.endswith(".sync.md"):
                continue
            scanned += 1
            path = os.path.join(sync_dir, name)
            for lineno, signature in scan(path):
                findings.append(
                    f"{feature}/{name}:{lineno}: `{signature}` nests a `{{ … }}` "
                    f"in its `then` — pass the authored result flat; the "
                    f"primary adapter serializes the response frame")

    if not scanned:
        print("SKIP  no sync specs found")
        return 0

    if findings:
        label = "WARN" if args.advisory else "FAIL"
        print(f"{label}  {len(findings)} sync `then` signature(s) carry a "
              f"transport frame:")
        for finding in findings:
            print(f"  - {finding}")
        return 0 if args.advisory else 1

    print(f"PASS  {scanned} sync spec(s) carry the authored result, not a frame")
    return 0


if __name__ == "__main__":
    sys.exit(main())
