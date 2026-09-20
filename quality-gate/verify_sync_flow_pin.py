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
  * Every other rule's `when` names the flow root as its **last** conjunct, with
    its route matcher (`requested: Web/request: [ route: "returns" ] => [ Routed ]`).
    It must be last: the engine calls the `where` evaluator with the rule's
    primary (first) conjunct as the trigger, so a pin placed before the domain
    trigger would bind `triggerField`/`triggerInput` to the request completion
    instead of the action the rule is about.
  * The route is required, and — when the feature's Stage 01b chains are present
    (the canonical source of the pin, `generate_syncs.py` derives it from row 1)
    — it must equal a route those chains actually root. A drifted route is the
    silent failure this caught: without a route a rule cannot tell one route's
    flow from another's, and with the wrong one it can never fire in its own.

Usage:
  python3 verify_sync_flow_pin.py --features-dir features

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

import artifact_parsers as ap


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


def route_of(when_cell):
    """The flow-root route a chain row declares (`route: "x"` or `POST /x`)."""
    match = re.search(r'route\s*:\s*"([^"]+)"', when_cell or "")
    if match:
        return match.group(1)
    match = re.search(r"\b([A-Z]+)\s+/([A-Za-z0-9_-]+)", when_cell or "")
    return match.group(2) if match else None


def chain_routes(features_dir, feature):
    """The routes the feature's Stage 01b chain tables root (row 1), if any."""
    chain_dir = os.path.join(features_dir, feature, "stages", "01b_chain-table", "output")
    if not os.path.isdir(chain_dir):
        return set()
    routes = set()
    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md") or fname.endswith("-all-scenarios-chain.md"):
            continue
        rows = ap.parse_chain_table(os.path.join(chain_dir, fname))
        if not rows:
            continue
        route = route_of(rows[0].when)
        if route:
            routes.add(route)
    return routes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Every non-bootstrap sync pins its flow root last")
    parser.add_argument("--features-dir", default="features")
    args = parser.parse_args()

    features_dir = os.path.abspath(args.features_dir)
    if not os.path.isdir(features_dir):
        print(f"SKIP  no features directory at {features_dir}")
        return 0

    failures = []
    pinned = bootstraps = 0
    known_routes = {}
    for feature, path in sync_files(features_dir):
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        block = WHEN_BLOCK.search(text)
        if not block:
            continue
        when = block.group(1)
        lines = when.splitlines()
        conjuncts = [i for i, line in enumerate(lines)
                     if CONJUNCT.match(line)]
        roots = [i for i, line in enumerate(lines) if FLOW_ROOT.search(line)]
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
        if len(roots) > 1:
            failures.append(
                f"{feature}/{name}: `when` names more than one flow root — a rule "
                "belongs to exactly one flow; a rule that must fire in two flows "
                "is two rules")
            continue
        root = roots[0]
        if not conjuncts or root != conjuncts[-1]:
            failures.append(
                f"{feature}/{name}: the flow root is not the LAST conjunct — the "
                "engine binds `triggerField`/`triggerInput` to the primary (first) "
                "conjunct, so a pin before the domain trigger blanks the rule's "
                "arguments")
            continue
        match = ROUTE.search(lines[root])
        if not match:
            failures.append(
                f"{feature}/{name}: pins the flow root without its route — two "
                "routes bootstrapping one action would still be one flow to this "
                "rule")
            continue
        route = match.group(1)
        if feature not in known_routes:
            known_routes[feature] = chain_routes(features_dir, feature)
        routes = known_routes[feature]
        if routes and route not in routes:
            failures.append(
                f"{feature}/{name}: pins route {route!r}, but the feature's chain "
                f"tables root {sorted(routes)} — the generator derives the pin "
                "from row 1, so this rule has drifted from its chain")
            continue
        pinned += 1

    if failures:
        print("FAIL  a non-bootstrap sync does not pin its flow root")
        for failure in failures[:12]:
            print(f"  - {failure}")
        if len(failures) > 12:
            print(f"  ... and {len(failures) - 12} more")
        return 1

    print(f"PASS  {pinned} non-bootstrap sync(s) pin their flow root last; "
          f"{bootstraps} bootstrap(s) are the flow root")
    return 0


if __name__ == "__main__":
    sys.exit(main())
