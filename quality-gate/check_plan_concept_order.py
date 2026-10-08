#!/usr/bin/env python3
"""
check_plan_concept_order.py — advisory planning check: warn when the plan
board sequences use cases in an order that guarantees corpus friction
(maintenance change `plan-concept-order-check`).

Why this exists:
  Which use case runs FIRST shapes the canonical concept corpus — the
  introducer's cut becomes the base every later feature extends. Two
  orderings are knowably bad at planning time:

  1. **Extension before introduction.** A feature scheduled early carries
     `extends:UC-XX` / `remodel:UC-XX` for a concept whose introducer UC is
     scheduled later (or not at all). The extend has nothing to extend; the
     plan forces either a re-sequence or a premature promotion.
  2. **Duplicate introduction.** Two features in the same planning wave
     (both `doing`/`next`) both propose the SAME concept as `new`. Gate 2
     promotion makes that a guaranteed collision: the second promoter hits
     the registry's one-introducer rule.

This check is part of the optional PLANNING overlay: it SKIPs (exit 0) when
`plan-board.md` is absent, and it NEVER blocks — sequencing is a human
call; the warnings exist so the call is made with the collisions visible.

Schedule order is derived from the board: `done` features are earliest,
then `doing`, `next`, `later`, `blocked`; ties break on Priority
(lower first), then slug (deterministic).

Usage:
  python3 check_plan_concept_order.py [--plan-board plan-board.md] \
                                      [--features-dir features]

Exit: 0 always (warn/skip/pass).
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402

STATUS_RANK = {"done": 0, "doing": 1, "next": 2, "later": 3, "blocked": 4}


def parse_plan_board(path):
    """Feature queue rows: [{slug, status, priority}], in file order."""
    rows = []
    with open(path, encoding="utf-8") as handle:
        in_table = False
        for line in handle:
            if line.lstrip().startswith("| Feature |"):
                in_table = True
                continue
            if in_table:
                if re.match(r"^\|[\s\-:]+\|", line):
                    continue
                if not line.startswith("|"):
                    in_table = False
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) < 3:
                    continue
                slug = cells[0].strip("`").strip()
                status = cells[1].strip().lower()
                try:
                    priority = int(cells[2])
                except ValueError:
                    priority = 99
                if slug and not slug.startswith("<"):
                    rows.append({"slug": slug, "status": status,
                                 "priority": priority})
    return rows


def schedule_key(row):
    return (STATUS_RANK.get(row["status"], 5), row["priority"], row["slug"])


def feature_origins(features_dir, slug):
    """{concept: origin} from a feature's responsibility map, if present."""
    resp = os.path.join(features_dir, slug, "stages",
                        "01a_responsibility-map", "output",
                        "responsibility-map.md")
    if not os.path.isfile(resp):
        return {}
    return {c: (e.origin or "").strip()
            for c, e in ap.parse_responsibility_map(resp).items()
            if c != "Web"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Advisory: plan-board orderings that guarantee corpus "
                    "friction")
    parser.add_argument("--plan-board", default="plan-board.md")
    parser.add_argument("--features-dir", default="features")
    args = parser.parse_args()

    if not os.path.isfile(args.plan_board):
        print("SKIP  no plan-board.md (planning overlay not in use)")
        return 0

    rows = parse_plan_board(args.plan_board)
    if not rows:
        print("SKIP  plan-board.md has no feature queue rows")
        return 0

    order = {row["slug"]: rank
             for rank, row in enumerate(sorted(rows, key=schedule_key))}
    origins = {row["slug"]: feature_origins(args.features_dir, row["slug"])
               for row in rows}

    warnings = []

    # 1. Extension/remodel/reuse scheduled before its concept's introducer.
    #    `reused:UC-XX` is a *consumer* dependency — the feature reads another
    #    feature's concept data — so the introducer must be scheduled earlier
    #    for it too, not only for an `extends`/`remodel`. (A consumer ordering
    #    the check previously missed.)
    for slug, concepts in sorted(origins.items()):
        for concept, origin in sorted(concepts.items()):
            match = re.match(r"(extends|remodel|reused):(UC-\S+)", origin,
                             re.IGNORECASE)
            if not match:
                continue
            kind_token = match.group(1).lower()
            introducer = match.group(2).rstrip("`").strip()
            if kind_token == "remodel":
                kind, verb = "remodels", "extend"
            elif kind_token == "extends":
                kind, verb = "extends", "extend"
            else:
                kind, verb = "reuses", "bind"
            if introducer == slug:
                continue
            if introducer not in order:
                warnings.append(
                    f"{slug} {kind} `{concept}` from "
                    f"{introducer}, which is not on the plan board at all — "
                    f"add it (scheduled earlier) or reconsider the origin")
            elif order[introducer] > order[slug]:
                warnings.append(
                    f"{slug} {kind} `{concept}` from "
                    f"{introducer}, but the board schedules {introducer} "
                    f"LATER — the feature has nothing to {verb}; re-sequence")

    # 2. Two features in the same active wave proposing the same NEW concept.
    active = [r["slug"] for r in rows if r["status"] in ("doing", "next")]
    proposals = {}
    for slug in sorted(active):
        for concept, origin in sorted(origins.get(slug, {}).items()):
            if origin.lower().startswith("new"):
                proposals.setdefault(concept, []).append(slug)
    for concept, slugs in sorted(proposals.items()):
        if len(slugs) > 1:
            warnings.append(
                f"`{concept}` is proposed as `new` by both "
                f"{' and '.join(slugs)} — a guaranteed Gate-2 collision; "
                f"pick one introducer")

    for warning in warnings:
        print(f"WARN  {warning}")
    if warnings:
        print(f"LINT  {len(warnings)} plan/concept ordering warning(s) "
              f"(advisory — exit 0)")
    else:
        print(f"PASS  plan board order is consistent with concept origins "
              f"({len(rows)} feature(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
