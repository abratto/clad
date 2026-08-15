#!/usr/bin/env python3
"""
approve_gate.py — Record human gate approval in RESUME.md.

Usage:
  python3 approve_gate.py --feature features/UC-XX-<slug> --gate 2
  python3 approve_gate.py --feature features/UC-XX-<slug> --iterative add-hostfirm
  python3 approve_gate.py --feature features/UC-XX-<slug> --gate 2 --baseline

Approval is bound to a content hash of the gate's stages: if the artefacts
are later re-derived, the approval becomes stale and the sequence guard will
force re-approval. `--baseline` records the hash for a gate that is already
approved without changing its status — used for the one-time migration of
features approved under the old (hash-less) workflow.

This is the ONLY way a gate should be marked as approved.
The agent MUST NOT edit RESUME.md directly to mark gates approved.
The agent MUST run this AFTER the human explicitly says "approved."
"""

import argparse
import os
import re
import sys

# Import the gate model + hash from the sibling module (same directory).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clad_stages as cs  # noqa: E402
from verify_stage_sequence import compute_gate_hash, gate_hash_recorded  # noqa: E402


GATE_LABELS = cs.GATE_LABELS


def _hash_line(gate_num: int, hash_hex: str) -> str:
    return f"- **Gate {gate_num} content hash:** `{hash_hex}`"


def _write_gate_hash(content: str, gate_num: int, hash_hex: str) -> str:
    """Insert or replace the content-hash line for a gate."""
    label = GATE_LABELS[gate_num]
    gate_pattern = rf"^- \*\*Gate {gate_num} \({re.escape(label)}\):\*\*"
    hash_pattern = rf"^- \*\*Gate {gate_num} content hash:\*\* `[0-9a-f]+`"
    new_line = _hash_line(gate_num, hash_hex)
    lines = content.splitlines(keepends=True)
    out = []
    hash_written = False
    for line in lines:
        if re.match(hash_pattern, line):
            if not hash_written:
                out.append(new_line + ("\n" if line.endswith("\n") else ""))
                hash_written = True
            continue
        out.append(line)
        if not hash_written and re.match(gate_pattern, line):
            out.append(new_line + "\n")
            hash_written = True
    if not hash_written:
        # No gate line found — append at end.
        out.append("\n" + new_line + "\n")
    return "".join(out)


def main():
    parser = argparse.ArgumentParser(
        description="Record human gate approval in RESUME.md")
    parser.add_argument("--feature", required=True, help="Feature root path")
    parser.add_argument("--gate", type=int, choices=[1, 2, 3],
                        help="Gate number (1/2/3). Not required with --iterative.")
    parser.add_argument("--iterative", default=None,
                        help="Iterative change name (e.g. add-hostfirm)")
    parser.add_argument("--baseline", action="store_true",
                        help="Record the content hash for an already-approved "
                             "gate without changing its status.")
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

        if args.baseline:
            recorded = gate_hash_recorded(content, args.gate)
            current = compute_gate_hash(args.feature, args.gate)
            if recorded == current:
                print(f"PASS  Gate {args.gate} ({label}) content hash already "
                      f"current (`{current[:12]}…`)")
            else:
                content = _write_gate_hash(content, args.gate, current)
                with open(resume_path, "w") as f:
                    f.write(content)
                print(f"PASS  Gate {args.gate} ({label}) baselined with content "
                      f"hash `{current[:12]}…`")
        else:
            content = re.sub(pattern, replacement, content)
            content = _write_gate_hash(content, args.gate,
                                       compute_gate_hash(args.feature, args.gate))
            with open(resume_path, "w") as f:
                f.write(content)
            print(f"PASS  Gate {args.gate} ({label}) approved in {resume_path}")
        print()
        print("  The agent may now proceed to the next stage.")

    sys.exit(0)


if __name__ == "__main__":
    main()
