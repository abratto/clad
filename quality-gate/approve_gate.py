#!/usr/bin/env python3
"""
approve_gate.py — Record human gate approval in RESUME.md.

Usage:
  python3 approve_gate.py --feature features/UC-XX-<slug> --gate 2

This is the ONLY way a gate should be marked as approved.
The agent MUST NOT edit RESUME.md directly to mark gates approved.
The agent MUST run this AFTER the human explicitly says "approved."
"""

import argparse
import os
import re
import sys


GATE_LABELS = {
    1: "Requirements",
    2: "Architecture",
    3: "Executable spec",
}


def main():
    parser = argparse.ArgumentParser(description="Record human gate approval in RESUME.md")
    parser.add_argument("--feature", required=True, help="Feature root path")
    parser.add_argument("--gate", required=True, type=int, choices=[1, 2, 3], help="Gate number")
    args = parser.parse_args()

    resume_path = os.path.join(os.path.abspath(args.feature), "RESUME.md")
    if not os.path.isfile(resume_path):
        print(f"FAIL  RESUME.md not found at {resume_path}")
        sys.exit(1)

    with open(resume_path) as f:
        content = f.read()

    label = GATE_LABELS[args.gate]
    pattern = rf"(- \*\*Gate {args.gate} \({re.escape(label)}\):\*\*) `\w+`"
    replacement = rf"\1 `approved`"

    if not re.search(pattern, content):
        print(f"FAIL  Gate {args.gate} ({label}) line not found in RESUME.md")
        sys.exit(1)

    content = re.sub(pattern, replacement, content)

    with open(resume_path, "w") as f:
        f.write(content)

    print(f"PASS  Gate {args.gate} ({label}) approved in {resume_path}")
    print(f"")
    print(f"  The agent may now proceed to the next stage.")
    sys.exit(0)


if __name__ == "__main__":
    main()
