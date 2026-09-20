#!/usr/bin/env python3
"""
verify_sync_flow_pin.py — every non-bootstrap sync names its flow root.

Why this exists:
  A flow token scopes a match to one flow, but *within* a flow any rule whose
  `when` matches fires. R11 scopes the bootstrap by route; the rule it triggers
  then inherits whatever flow it lands in, and nothing checks that it belongs
  there. So two use cases sharing a completion fire each other's rules — UC-03's
  `lend` fired in UC-04's return flow and UC-04's `close` fired in UC-03's borrow
  flow, surfacing only at Stage 04e-green.

  The paper's `RegistrationError` names the request, matcher and all (§5.3:
  "other web requests may be in process at the same time"), and every ConceptBox
  rule does the same ("Multiple When Clauses: Handling Request Flow"). See
  maintenance/sync-flow-pinning.md.

Checks (per feature):
  * A bootstrap — a rule whose `when` is a single `Web/request` completion — IS
    the flow root, so it carries no pin.
  * Every other rule's `when` names the flow root as a conjunct, with its route
    matcher (`requested: Web/request: [ route: "returns" ] => [ Routed ]`).
    The route is required: without it a rule cannot tell one route's flow from
    another's, which is the defect this guards.

Usage:
  python3 verify_sync_flow_pin.py --features-dir features

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys


WHEN_BLOCK = re.compile(r"when\s*\{(.*?)\}", re.DOTALL)
# One `[name: ]Concept/action:` conjunct per line in the rule block.
CONJUNCT = re.compile(r"^\s*(?:\w+\s*:\s*)?([A-Za-z]+)/([A-Za-z]+)\s*:", re.MULTILINE)
FLOW_ROOT = re.compile(r"Web/request\s*:\s*\[([^\]]*)\]")
ROUTE = re.compile(r'route\s*:\s*"([^"]+)"')


def sync_files(features_dir):
    for name in sorted(os.listdir(features_dir)):
        feature = os.path.join(features_dir, name)
        out = os.path.join(feature, "stages", "03_syncs", "output")
        if not os.path.isdir(out):
            continue
        for fname in sorted(os.listdir(out)):
            if fname.endswith(".sync.md"):
                yield name, os.path.join(out, fname)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Every non-bootstrap sync pins its flow root")
    parser.add_argument("--features-dir", default="features")
    args = parser.parse_args()

    features_dir = os.path.abspath(args.features_dir)
    if not os.path.isdir(features_dir):
        print(f"SKIP  no features directory at {features_dir}")
        return 0

    failures = []
    pinned = bootstraps = 0
    for feature, path in sync_files(features_dir):
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        block = WHEN_BLOCK.search(text)
        if not block:
            continue
        when = block.group(1)
        roots = FLOW_ROOT.findall(when)
        conjuncts = CONJUNCT.findall(when)
        name = os.path.basename(path)

        # A lone `Web/request` conjunct IS the flow root: the bootstrap.
        if len(conjuncts) <= 1 and roots:
            bootstraps += 1
            continue

        if not roots:
            failures.append(
                f"{feature}/{name}: `when` never names the flow root — this rule "
                "cannot be told apart from another use case's rule on the same "
                "completion")
            continue
        if not ROUTE.search(roots[0]):
            failures.append(
                f"{feature}/{name}: pins the flow root without its route — two "
                "routes bootstrapping one action would still be one flow to this "
                "rule")
            continue
        pinned += 1

    if failures:
        print("FAIL  a non-bootstrap sync does not pin its flow root")
        for failure in failures[:12]:
            print(f"  - {failure}")
        if len(failures) > 12:
            print(f"  ... and {len(failures) - 12} more")
        return 1

    print(f"PASS  {pinned} non-bootstrap sync(s) pin their flow root; "
          f"{bootstraps} bootstrap(s) are the flow root")
    return 0


if __name__ == "__main__":
    sys.exit(main())
