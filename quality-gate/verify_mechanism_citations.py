#!/usr/bin/env python3
"""
verify_mechanism_citations.py — a mechanism claim cites the code it rests on.

Why this exists:
  A maintenance record or methodology doc can state a *mechanism* the code does
  not support — the flow-pin record claimed the engine "never re-evaluates"; it
  does (`SyncEngine.processInvocation` re-checks on every conjunct completion).
  Nothing caught that wrong explanation, and it survived into the docs. The code
  path the claim rests on would have caught it: citing it forces the author to
  look. This check requires the mechanism sections to cite a code path
  (`path/File.java:LINE` or `File#symbol`).

Checks:
  * `maintenance/*.md` with `Change class` platform|mixed and `Status` active
    MUST carry a `## Mechanism` section with at least one code citation
    (a closed record is grandfathered, and warns).
  * `SYNCHRONIZATIONS.md` `## Naming` and `### Flow pinning` MUST each cite at
    least one code path — they are the load-bearing mechanism sections.

Usage:
  python3 verify_mechanism_citations.py --maintenance-dir maintenance \
      --sync-doc methodology/architecture/SYNCHRONIZATIONS.md

Exit: 1 if an active record or a checked section has no citation; 0 otherwise.
"""

import argparse
import os
import re
import sys

# A code citation: a file path/name with a line (`:12`) or symbol (`#method`).
CITATION = re.compile(
    r"[\w./-]+\.(?:java|py|kt|scala|ts|js)(?::\d+|#[\w.]+)")
PLATFORM_CLASSES = {"platform", "mixed"}


def field(text, label):
    match = re.search(rf"^- \*\*{re.escape(label)}:\*\*\s*`?([^`\n]+)`?\s*$",
                      text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def section_body(text, heading):
    """Body of the section whose heading line is exactly `heading`, up to the
    next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    out, capturing = [], False
    for line in lines:
        m = re.match(r"^(#{1,6})\s", line)
        if m:
            if capturing:
                break
            if line.strip() == heading.strip():
                capturing = True
            continue
        if capturing:
            out.append(line)
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mechanism claims cite code")
    parser.add_argument("--maintenance-dir", default="maintenance")
    parser.add_argument(
        "--sync-doc", default="methodology/architecture/SYNCHRONIZATIONS.md")
    args = parser.parse_args()

    failures, closed_missing = [], 0

    if os.path.isdir(args.maintenance_dir):
        for name in sorted(os.listdir(args.maintenance_dir)):
            if not name.endswith(".md"):
                continue
            path = os.path.join(args.maintenance_dir, name)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            if field(text, "Change class").lower() not in PLATFORM_CLASSES:
                continue
            body = section_body(text, "## Mechanism")
            cited = bool(CITATION.search(body))
            status = field(text, "Status").lower()
            if cited:
                continue
            if status == "active":
                failures.append(
                    f"{path}: active platform change has no `## Mechanism` "
                    f"section citing a code path (`file.java:LINE` / "
                    f"`File#symbol`)")
            else:
                closed_missing += 1

    if os.path.isfile(args.sync_doc):
        with open(args.sync_doc, encoding="utf-8") as handle:
            doc = handle.read()
        for heading in ("## Naming", "### Flow pinning"):
            if not CITATION.search(section_body(doc, heading)):
                failures.append(
                    f"{args.sync_doc} {heading}: no code-path citation — a "
                    f"mechanism claim here must point at the code it rests on")

    if closed_missing:
        print(f"WARN  {closed_missing} closed platform record(s) predate the "
              f"`## Mechanism` requirement (grandfathered)")
    if failures:
        print(f"FAIL  {len(failures)} mechanism claim(s) without a citation:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS  mechanism claims cite their code path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
