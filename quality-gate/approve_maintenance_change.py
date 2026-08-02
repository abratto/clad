#!/usr/bin/env python3
"""Record explicit human approval of a maintenance design or evidence gate."""

import argparse
import re
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Approve a maintenance-change gate.")
    parser.add_argument("--change", required=True, help="Path to maintenance/<change-name>.md")
    parser.add_argument("--gate", required=True, choices=("design", "evidence"))
    args = parser.parse_args()

    path = Path(args.change)
    if not path.is_file():
        print(f"FAIL  maintenance record not found: {path}")
        sys.exit(1)

    label = "Design gate" if args.gate == "design" else "Evidence gate"
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        rf"(- \*\*{re.escape(label)}:\*\*) `(?:pending|approved)`",
        r"\1 `approved`", text)
    if count != 1:
        print(f"FAIL  expected one `{label}` field in {path}")
        sys.exit(1)
    path.write_text(updated, encoding="utf-8")
    print(f"PASS  {label.lower()} approved in {path}")


if __name__ == "__main__":
    main()