#!/usr/bin/env python3
"""
verify_chain_outcomes.py — Stage 01b gate: every chain-table completion
resolves against the concept spec that owns it.

Why this exists:
  A chain row names a trigger (`Concept.action[Completion]`) and a target
  action. The action name is checked against the 01a map
  (`verify_chain_map_names.py`); the *completion* is not checked against the
  concept that must produce it. So a `reused` concept whose canonical spec does
  not declare the completion (e.g. a read action that only has an `OK` outcome,
  invoked on a failure branch) sails through Gate 1, and the dead-end surfaces
  only much later — as a chain note punted to the human, or an outcome the
  concept never emits.

  The fix is a design-time check: every `When` conjunct's
  `Concept.action[Completion]` must be declared by that concept's spec (the
  feature's own Stage-02 proposal shadows the canonical corpus by name). When a
  `reused` concept lacks the completion, the remedy is to propose an `extends`
  and reopen Stage 01a — the concept cannot gain an outcome by reuse.

Web is exempt (the bootstrap concept's `request`/`respond` surface is owned by
the transport profile).

Usage:
  python3 verify_chain_outcomes.py --resp-map <01a> --chain-dir <01b> \
                                   --concept-dir <02_concepts/output> \
                                   --concept-dir <canonical corpus>

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402


def _completion_base(token: str) -> str:
    """`OK` -> `OK`, `VALID(accountId)` -> `VALID`, `error: "x"` -> `error`."""
    return re.split(r"[:\s(]", (token or "").strip(), 1)[0].strip()


def spec_actions(path: str):
    """`{action: set(completion bases)}` from a concept spec's `## Actions`."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    section = re.search(r"^##\s+Actions\s*$(.*?)(?=^##\s|\Z)", text,
                        re.MULTILINE | re.DOTALL)
    actions = {}
    for action, outs in re.findall(
            r"^([a-z][A-Za-z0-9]*)\s*\[[^\]]*\]\s*=>\s*\[([^\]]*)\]",
            section.group(1) if section else "", re.MULTILINE):
        bases = actions.setdefault(action, set())
        for token in outs.split(";"):
            base = _completion_base(token)
            if base:
                bases.add(base)
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chain-table completions must resolve against the concept spec")
    parser.add_argument("--resp-map", required=True)
    parser.add_argument("--chain-dir", required=True)
    parser.add_argument("--concept-dir", action="append", default=[],
                        help="Repeatable; earlier dirs shadow later by name")
    args = parser.parse_args()

    if not os.path.isfile(args.resp_map):
        print("SKIP  no responsibility map (Stage 01a not reached)")
        return 0
    if not os.path.isdir(args.chain_dir):
        print("SKIP  no chain-table output (Stage 01b not reached)")
        return 0

    spec_paths = ap.concept_spec_paths([d for d in args.concept_dir
                                        if os.path.isdir(d)])
    if not spec_paths:
        print("SKIP  no concept specs to resolve completions against")
        return 0

    origins = {c: (e.origin or "").strip().lower()
               for c, e in ap.parse_responsibility_map(args.resp_map).items()}

    checked = 0
    failures = []
    for chain in sorted(os.listdir(args.chain_dir)):
        if not chain.endswith("-chain.md"):
            continue
        for row in ap.parse_chain_table(os.path.join(args.chain_dir, chain)):
            for conjunct in row.conjuncts:
                concept, action = conjunct.concept, conjunct.action
                if concept == "Web" or concept not in spec_paths:
                    continue
                spec = spec_actions(spec_paths[concept])
                if action not in spec:
                    failures.append(
                        f"{chain}: row {row.row_num} invokes `{concept}.{action}` "
                        f"but `{concept}` declares no such action")
                    continue
                base = _completion_base(conjunct.outcome)
                if not base:
                    continue
                checked += 1
                if base.lower() not in {b.lower() for b in spec[action]}:
                    origin = origins.get(concept, "")
                    if origin.startswith("reused"):
                        failures.append(
                            f"{chain}: row {row.row_num} triggers on "
                            f"`{concept}.{action}[{base}]`, but `{concept}` is "
                            f"`reused` and its canonical spec declares no "
                            f"`{base}` completion — a reused concept cannot gain "
                            f"an outcome. Propose an `extends` for `{concept}` "
                            f"and reopen Stage 01a.")
                    else:
                        failures.append(
                            f"{chain}: row {row.row_num} triggers on "
                            f"`{concept}.{action}[{base}]`, but the `{concept}` "
                            f"proposal declares no `{base}` completion")

    if failures:
        print(f"FAIL  {len(failures)} chain completion(s) the owning concept "
              f"does not declare:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS  {checked} chain completion(s) resolve against their concept specs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
