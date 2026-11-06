#!/usr/bin/env python3
"""
verify_sync_matrix.py — Stage 03 gate: every sync has a complete Sync Contract
Matrix, a well-formed `when`/`then` rule, and matrix rows that resolve against
the chain table.

Why this exists:
  Each sync spec must document its derivation from the approved chain table:
  source/target row IDs, when/then signatures, and allowed literals. An LLM can
  forget the matrix, leave fields empty, or — worse — keep a valid-looking
  matrix while the rule body itself is unparseable. The matrix shape checks and
  the graph/transition checks then pass with nothing to analyse (a silent false
  green: "Stage 03 can accept a malformed sync rule").

Checks:
  1. `## Sync Contract Matrix` heading + the required columns (by NAME, not
     position): Source row, Target row, when, then, Allowed literals.
  2. Every data row is complete (row IDs non-empty; when/then non-empty; every
     `∧` conjunct of a joined `when` non-empty).
  3. The rule body parses into a SyncSpec with at least one complete `when`
     conjunct and at least one `then` target (`artifact_parsers.sync_spec_problems`).
  4. When `--chain-dir` is given, every source/target row ID must exist in the
     chain table, and the matrix's `when`/`then` signatures must name the source
     row's `when` action and the target row's `then` action respectively.

Usage:
  python3 verify_sync_matrix.py --sync-dir <sync-output/> --chain-dir <chain-output/>
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import check_runner as cr  # noqa: E402

REQUIRED_COLUMNS = ("Source row", "Target row", "when", "then", "Allowed literals")


def _norm(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").strip().lower())


def _matrix_table(lines):
    """`(header_names, [data_cell_lists])` for the Sync Contract Matrix table."""
    start = None
    for i, line in enumerate(lines):
        if "## Sync Contract Matrix" in line:
            start = i
            break
    if start is None:
        return None, []
    header, rows = None, []
    seen_sep = False
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("## ") and i > start + 1:
            break
        if not line.strip():
            if header is not None and rows:
                break
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if re.match(r"^[\s\-:]+$", cells[0]):
            seen_sep = True
            continue
        if seen_sep:
            rows.append(cells)
    return header, rows


def _action_norm(cell):
    """The first `Concept/action` (or `Concept.action`) in a chain cell."""
    m = re.search(r"([A-Za-z][A-Za-z0-9]*)\s*[/.]\s*([A-Za-z][A-Za-z0-9]*)", cell)
    return _norm(f"{m.group(1)}{m.group(2)}") if m else ""


def _chain_rows(chain_dir):
    """`{row_id: (when_action_norm, then_action_norm)}` across chain tables.

    Row IDs are read from the raw `#` column so a lettered id (`3b`, `4a`) is
    captured — `parse_chain_table` only keeps numeric rows."""
    rows = {}
    if not chain_dir or not os.path.isdir(chain_dir):
        return rows
    for name in sorted(os.listdir(chain_dir)):
        # Include the consolidated `-all-scenarios-chain.md` too: sync matrices
        # cite its lettered row ids (`3b`, `4a`), which the per-scenario chains
        # (numeric only) do not carry.
        if not name.endswith("-chain.md"):
            continue
        with open(os.path.join(chain_dir, name), encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        header, data = None, []
        for line in lines:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                low = [c.replace("`", "").strip().lower() for c in cells]
                if "#" in low and "when" in low and "then" in low:
                    header = low
                continue
            if re.match(r"^[\s\-:]+$", cells[0]):
                continue
            data.append(cells)
        if not header:
            continue
        wi, ti, ni = header.index("when"), header.index("then"), header.index("#")
        for row in data:
            if len(row) <= max(wi, ti, ni):
                continue
            rid = row[ni].strip("`").strip()
            if rid:
                rows[rid] = (_action_norm(row[wi]), _action_norm(row[ti]))
    return rows


def check_sync_matrix(sync_dir, chain_dir=None):
    """Return a list of (filename, message) failures."""
    failures = []
    if not os.path.isdir(sync_dir):
        return [("(no files)", f"sync directory not found: {sync_dir}")]
    chain = _chain_rows(chain_dir)

    for fname in sorted(os.listdir(sync_dir)):
        if not fname.endswith(".sync.md"):
            continue
        path = os.path.join(sync_dir, fname)

        # Check 3 first: a malformed rule body is the silent false green.
        spec = ap.parse_sync(path)
        for problem in ap.sync_spec_problems(spec):
            failures.append((fname, f"malformed sync rule: {problem}"))

        with open(path, encoding="utf-8") as f:
            content = f.read()
        if "## Sync Contract Matrix" not in content:
            failures.append((fname, "missing ## Sync Contract Matrix heading"))
            continue

        header, rows = _matrix_table(content.split("\n"))
        if not header:
            failures.append((fname, "Sync Contract Matrix table header not found"))
            continue
        # Columns are matched by name, tolerant of backticks (`when` signature).
        header_norm = [h.replace("`", "").strip().lower() for h in header]

        def _col(name):
            for i, h in enumerate(header_norm):
                if name.lower() in h:
                    return i
            return -1

        missing_cols = [c for c in REQUIRED_COLUMNS if _col(c) < 0]
        if missing_cols:
            failures.append(
                (fname, "matrix missing column(s): " + ", ".join(missing_cols)))
            continue
        if not rows:
            failures.append((fname, "Sync Contract Matrix table has no data rows"))
            continue

        idx = {name: _col(name) for name in REQUIRED_COLUMNS}
        for row in rows:
            if len(row) < len(header):
                failures.append((fname, f"matrix row has {len(row)} of "
                                        f"{len(header)} cells"))
                continue
            source_row = row[idx["Source row"]].strip("`").strip()
            target_row = row[idx["Target row"]].strip("`").strip()
            when_sig = row[idx["when"]].strip("`").strip()
            then_sig = row[idx["then"]].strip("`").strip()

            if not source_row or not target_row:
                failures.append((fname, f"empty row IDs: source='{source_row}', "
                                        f"target='{target_row}'"))
            if not when_sig:
                failures.append((fname, "empty `when` signature"))
            if not then_sig:
                failures.append((fname, "empty `then` signature"))
            if "\u2227" in when_sig and any(
                    not part.strip() for part in when_sig.split("\u2227")):
                failures.append((fname, "joined `when` signature has an empty conjunct"))

            if not chain:
                continue
            # Cross-reference the row IDs and signatures against the chain table.
            for label, rid in (("source", source_row), ("target", target_row)):
                if rid and rid not in chain:
                    failures.append((fname, f"{label} row `{rid}` does not exist in "
                                            f"the chain table"))
            # A sync is triggered by the source row's `then` completion and
            # performs the target row's `then` action.
            if source_row in chain:
                want = chain[source_row][1]
                if want and want not in _norm(when_sig):
                    failures.append(
                        (fname, f"`when` signature does not name chain row "
                                f"{source_row}'s `then` action ({want})"))
            if target_row in chain:
                want = chain[target_row][1]
                if want and want not in _norm(then_sig):
                    failures.append(
                        (fname, f"`then` signature does not name chain row "
                                f"{target_row}'s `then` action ({want})"))

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
                            help="Path to 01b_chain-table/output/ — row IDs and "
                                 "signatures are cross-referenced against it")

    def body(args: argparse.Namespace) -> cr.Verdict:
        failures = check_sync_matrix(args.sync_dir, args.chain_dir)

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
