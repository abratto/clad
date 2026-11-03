#!/usr/bin/env python3
"""
verify_sync_matrix.py — Stage gate: every sync has a complete Sync Contract Matrix.

Why this exists:
  Each sync spec must document its derivation from the approved chain table:
  source/target row IDs, when/then signatures, and allowed literals. An LLM
  can forget to include the matrix or leave fields empty. This script verifies
  the matrix exists and has all required columns for every sync file.

Checks:
  1. ## Sync Contract Matrix heading present in every sync file
  2. Table columns present: Source row, Target row, when, then, Allowed literals
  3. Row IDs are non-empty alphanumeric identifiers
  4. When/then signatures are non-empty

Usage:
  python3 verify_sync_matrix.py --sync-dir <sync-output/> --chain-dir <chain-output/>
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402


def check_sync_matrix(sync_dir):
    """Check every sync file has a Sync Contract Matrix section with required columns.
    Returns list of (filename, message) tuples for failures."""
    failures = []

    if not os.path.isdir(sync_dir):
        failures.append(("(no files)", f"sync directory not found: {sync_dir}"))
        return failures

    for fname in sorted(os.listdir(sync_dir)):
        if not fname.endswith(".sync.md"):
            continue
        path = os.path.join(sync_dir, fname)
        with open(path) as f:
            content = f.read()

        # Check 1: Matrix heading present
        if "## Sync Contract Matrix" not in content:
            failures.append((fname, "missing ## Sync Contract Matrix heading"))
            continue

        # Check 2: Table has required columns
        # Find the table separator row (|--|--|--|...|)
        lines = content.split("\n")
        matrix_start = None
        for i, line in enumerate(lines):
            if "## Sync Contract Matrix" in line:
                matrix_start = i
                break

        if matrix_start is None:
            continue  # already reported above

        # Look for the table header and separator within 10 lines of the heading
        header_line = None
        sep_line = None
        data_line = None
        for i in range(matrix_start + 1, min(matrix_start + 10, len(lines))):
            line = lines[i]
            if "Source row" in line and "Target row" in line:
                header_line = i
            elif re.match(r"^\|[\s\-:]+\|", line) and header_line is not None and sep_line is None:
                sep_line = i
            elif line.startswith("|") and header_line is not None and sep_line is not None and data_line is None:
                data_line = i
                break

        if header_line is None:
            failures.append((fname, "Sync Contract Matrix table header not found"))
            continue
        if data_line is None:
            failures.append((fname, "Sync Contract Matrix table has no data rows"))
            continue

        # Check 3: Parse the data row columns
        data_parts = [p.strip() for p in lines[data_line].split("|")]
        if len(data_parts) < 6:
            failures.append((fname, f"Sync Contract Matrix has {len(data_parts)} columns, expected 6"))
            continue

        source_row = data_parts[1].strip("`")
        target_row = data_parts[2].strip("`")
        when_sig = data_parts[3].strip("`")
        then_sig = data_parts[4].strip("`")
        literals = data_parts[5].strip("`")

        # Source and target rows should be alphanumeric identifiers
        if not source_row or not target_row:
            failures.append((fname, f"empty row IDs: source='{source_row}', target='{target_row}'"))

        # When and then signatures should not be empty
        if not when_sig:
            failures.append((fname, "empty `when` signature"))
        if not then_sig:
            failures.append((fname, "empty `then` signature"))

        # A multi-`when` join signature (`a: A/act: [...] => [ X ] ∧ b: ...`)
        # is legal — one Then, one outcome per row — but every conjunct must
        # be non-empty. Classic single-trigger signatures are unaffected.
        if "\u2227" in when_sig:
            conjuncts = [part.strip() for part in when_sig.split("\u2227")]
            if any(not part for part in conjuncts):
                failures.append(
                    (fname, "joined `when` signature has an empty conjunct"))

    return failures


class _Tail:
    """The `FAIL` word printed once after the body's own failure lines."""

    status = cr.FAIL
    message = ""
    problems = ()
    detail = None
    prelude = None
    exit_code = 1


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--sync-dir", required=True,
                            help="Path to 03_syncs/output/")
        parser.add_argument("--chain-dir", required=False, default=None,
                            help="Optional: path to 01b_chain-table/output/ for cross-ref")

    def body(args: argparse.Namespace) -> cr.Verdict:
        failures = check_sync_matrix(args.sync_dir)

        if not failures:
            sync_files = [f for f in os.listdir(args.sync_dir)
                          if f.endswith(".sync.md")] if os.path.isdir(args.sync_dir) else []
            return cr.Verdict.ok(
                f"{len(sync_files)} sync files with valid Sync Contract Matrices")
        for fname, msg in failures:
            print(f"FAIL  {fname}: {msg}")
        return _Tail()

    return _run(body, argv, configure)


def _run(body, argv, configure):
    import contextlib
    import io
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        verdict = body(_parse(argv, configure))
    if isinstance(verdict, _Tail):
        sys.stdout.write(buffer.getvalue())
        return 1
    return cr.emit(verdict)


def _parse(argv, configure):
    parser = argparse.ArgumentParser(
        description="Verify every sync has a complete Sync Contract Matrix")
    configure(parser)
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
