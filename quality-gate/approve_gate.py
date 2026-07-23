#!/usr/bin/env python3
"""
approve_gate.py — Record human gate approval in RESUME.md.

Usage:
  python3 approve_gate.py --feature features/UC-XX-<slug> --gate 2
  python3 approve_gate.py --feature features/UC-XX-<slug> --iterative add-hostfirm

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
    parser = argparse.ArgumentParser(
        description="Record human gate approval in RESUME.md")
    parser.add_argument("--feature", required=True, help="Feature root path")
    parser.add_argument("--gate", type=int, choices=[1, 2, 3],
                        help="Gate number (1/2/3). Not required with --iterative.")
    parser.add_argument("--iterative", default=None,
                        help="Iterative change name (e.g. add-hostfirm)")
    args = parser.parse_args()

    if not args.gate and not args.iterative:
        print("FAIL  either --gate or --iterative is required")
        sys.exit(1)

    resume_path = os.path.join(os.path.abspath(args.feature), "RESUME.md")
    if not os.path.isfile(resume_path):
        print(f"FAIL  RESUME.md not found at {resume_path}")
        sys.exit(1)

    with open(resume_path) as f:
        content = f.read()

    if args.iterative:
        # Record the iterative change as reviewed
        iterative_line = f"- **Iterative change `{args.iterative}`:** `approved`"
        if iterative_line in content:
            print(f"PASS  iterative change `{args.iterative}` already approved")
        else:
            # Insert before the first gate line or append to the gate snapshot
            gate_pattern = r"(- \*\*Gate \d)"
            m = re.search(gate_pattern, content)
            if m:
                content = (content[:m.start()]
                           + iterative_line + "\n"
                           + content[m.start():])
            else:
                content += "\n" + iterative_line + "\n"
            with open(resume_path, "w") as f:
                f.write(content)
            print(f"PASS  iterative change `{args.iterative}` approved "
                  f"in {resume_path}")
        print()
        print("  The agent may now commit the changed files + _changes/ artefact.")
    else:
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
        print()
        print("  The agent may now proceed to the next stage.")

    sys.exit(0)


if __name__ == "__main__":
    main()
