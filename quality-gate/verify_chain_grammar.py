#!/usr/bin/env python3
"""Verify the lossless, one-branch grammar of Stage 01b chain tables."""

import argparse
import os
import re
import sys

from artifact_parsers import AND, parse_chain_table

# Mirrors parse_chain_table's Then regex (leading backtick required, suffix
# optional) so a legal classic cell is never miscounted.
_THEN_REF_RE = re.compile(r"`([A-Za-z]+)\.([A-Za-z]+)(\[[^\]]*\])?")


def main():
    parser = argparse.ArgumentParser(
        description="Verify one explicit outcome token per chain-table row")
    parser.add_argument("--chain-dir", required=True)
    args = parser.parse_args()

    failures = []
    checked = 0
    for filename in sorted(os.listdir(args.chain_dir)):
        if (not filename.endswith("-chain.md")
            or filename.endswith("-all-scenarios-chain.md")):
            continue
        path = os.path.join(args.chain_dir, filename)
        for row in parse_chain_table(path):
            checked += 1
            if len(row.outcome_tokens) != 1:
                failures.append(
                    f"{filename}:{row.row_num}: Outcome must contain exactly "
                    f"one backticked token (found {len(row.outcome_tokens)})")
                continue
            if "|" in row.outcome_tokens[0]:
                failures.append(
                    f"{filename}:{row.row_num}: Outcome token must not use "
                    "pipe-separated union syntax; add one row per branch")
                continue
            # Exactly one `Then` action reference per row.
            then_refs = _THEN_REF_RE.findall(row.then_raw)
            if len(then_refs) != 1:
                failures.append(
                    f"{filename}:{row.row_num}: `Then` must contain exactly "
                    f"one backticked Concept.action (found {len(then_refs)})")
            # A composite `When` (join) is legal: >=1 `∧`-separated conjuncts,
            # each `[name: ]Concept/action[Outcome]`, still with one Then.
            if row.composite_when:
                parts = [p for p in row.when.replace("`", "").split(AND)
                         if p.strip()]
                if len(parts) < 2 or len(row.conjuncts) != len(parts):
                    failures.append(
                        f"{filename}:{row.row_num}: composite `When` must "
                        f"declare >=2 well-formed `∧`-separated conjuncts "
                        f"(found {len(row.conjuncts)} parsed of "
                        f"{len(parts)} parts)")

    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        sys.exit(1)
    print(f"PASS  {checked} chain-table rows use one explicit outcome token")


if __name__ == "__main__":
    main()