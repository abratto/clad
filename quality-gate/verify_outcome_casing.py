#!/usr/bin/env python3
"""verify_outcome_casing.py — authored outcome tokens are SCREAMING_SNAKE_CASE.

Why this exists:
  `FLOW_TOKENS.md` §"Outcome casing" states the convention: the canonical,
  profile-agnostic outcome token is SCREAMING_SNAKE_CASE, and it is used in the
  chain tables, concept specs, contracts, derivation maps, and the Acceptance
  Spec. The
  runtime profile may emit a different casing (e.g. java-legible PascalCase) and
  comparisons normalise — but the AUTHORED artefacts must agree so a worker
  never has to guess whether to write `Ok` or `OK` (experiment defect D9/D26:
  contracts were SCREAMING while chain tables and specs were PascalCase, and the
  mismatch surfaced as test/feature failures across every use case).

  This check runs where the tokens are authored: Stage 01b (chain tables) and
  Stage 02 (concept specs).

Usage:
  python3 verify_outcome_casing.py --feature features/UC-XX-<slug>
Exit: 0 pass/skip, 1 a non-SCREAMING authored outcome token.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import check_runner as cr  # noqa: E402
import clad_stages as cs  # noqa: E402

SCREAMING = re.compile(r"^[A-Z][A-Z0-9_]*$")
# Concept specs declare the flow-token outcome on `outcome: "Token"`.
SPEC_FLOW_OUTCOME = re.compile(r'outcome:\s*"([A-Za-z0-9_]+)"')


def _is_bad(token: str) -> bool:
    token = token.strip().strip("`")
    if not token or token.startswith("<"):
        return False
    if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", token):
        return False  # not an outcome-shaped token (e.g. a payload)
    return not SCREAMING.match(token)


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--feature", required=True)

    def body(args: argparse.Namespace) -> cr.Verdict:
        feature_root = os.path.abspath(args.feature)
        failures = []

        chain_dir = cs.CHAIN_DIR(feature_root)
        if os.path.isdir(chain_dir):
            for filename in sorted(os.listdir(chain_dir)):
                if not filename.endswith("-chain.md"):
                    continue
                for row in ap.parse_chain_table(os.path.join(chain_dir, filename)):
                    for token in (row.outcome_bases or [row.outcome_base]):
                        if _is_bad(token):
                            failures.append(cr.Problem(
                                f"outcome `{token.strip()}`",
                                where=f"{filename} row {row.row_num}"))

        # Resolve the corpus union (feature proposals shadow the canonical
        # corpus), so both the authored proposals and the canonical specs are
        # checked.
        seen_concepts: set[str] = set()
        for concept_dir in cs.concept_source_dirs(feature_root):
            if not os.path.isdir(concept_dir):
                continue
            for filename in sorted(os.listdir(concept_dir)):
                if not filename.endswith(".concept.md") or filename in seen_concepts:
                    continue
                seen_concepts.add(filename)
                with open(os.path.join(concept_dir, filename), encoding="utf-8") as fh:
                    text = fh.read()
                for token in SPEC_FLOW_OUTCOME.findall(text):
                    if _is_bad(token):
                        failures.append(cr.Problem(
                            f"{filename}: flow-token outcome `{token}`"))

        if not os.path.isdir(chain_dir) and not seen_concepts:
            return cr.Verdict.skip("no chain tables or concept specs to check")
        if failures:
            verdict = cr.Verdict.fail(
                f"{len(failures)} authored outcome token(s) are not "
                f"SCREAMING_SNAKE_CASE", failures)
            verdict.detail = (
                '      Per FLOW_TOKENS.md §"Outcome casing", authored outcome '
                "tokens are SCREAMING_SNAKE_CASE\n"
                "      (the runtime profile may emit another casing; "
                "comparisons normalise).")
            return verdict
        return cr.Verdict.ok("authored outcome tokens are SCREAMING_SNAKE_CASE")

    return cr.run_check(
        "Authored outcome tokens must be SCREAMING_SNAKE_CASE",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
