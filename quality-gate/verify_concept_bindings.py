#!/usr/bin/env python3
"""
verify_concept_bindings.py — Stage 02 gate: `concept-bindings.md` agrees with
the Stage 01a responsibility map and resolves against the concept specs.

Why this exists:
  `concept-bindings.md` is emitted by every feature and is the source the
  concepts-catalog derives its "Used by" column from. Nothing parsed its rows,
  so a binding could name a concept the responsibility map never declared, carry
  an `Origin` the map disagrees with, or list an action the concept does not
  have — and the catalog would then record a use that never passed Gate 1.

  The check: every binding row's concept appears in the 01a map with the same
  `Origin`, and every listed action exists in the concept's spec (the feature's
  Stage-02 proposal shadows the canonical corpus by name).

Usage:
  python3 verify_concept_bindings.py --feature features/UC-XX-<slug>

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402
import clad_stages as cs  # noqa: E402


def parse_bindings(path: str):
    """`[(concept, origin, [actions])]` from `concept-bindings.md`."""
    rows = []
    in_table = False
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.lstrip().startswith("| Concept |") and "Origin" in line:
                in_table = True
                continue
            if not in_table:
                continue
            if not line.startswith("|"):
                break
            if re.match(r"^\|[\s\-:]+\|", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0] and not cells[0].startswith("<"):
                rows.append((cells[0].strip("`"), cells[1].strip("`"),
                             re.findall(r"`([^`]+)`", cells[2])))
    return rows


def spec_actions(path: str):
    """`{action: set(completion bases)}` from a concept spec's `## Actions`."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    section = re.search(r"^##\s+Actions\s*$(.*?)(?=^##\s|\Z)", text,
                        re.MULTILINE | re.DOTALL)
    return {m.group(1) for m in re.finditer(
        r"^([a-z][A-Za-z0-9]*)\s*\[[^\]]*\]\s*=>", section.group(1) if section else "",
        re.MULTILINE)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="concept-bindings.md agrees with the 01a map")
    parser.add_argument("--feature", required=True)
    args = parser.parse_args()

    feature = os.path.abspath(args.feature)
    bindings = os.path.join(cs.output_dir(feature, "02_concepts"),
                            "concept-bindings.md")
    resp_map = os.path.join(cs.output_dir(feature, "01a_responsibility-map"),
                            "responsibility-map.md")
    if not os.path.isfile(bindings):
        print("SKIP  no concept-bindings.md (Stage 02 not reached)")
        return 0
    if not os.path.isfile(resp_map):
        print("SKIP  no responsibility map (Stage 01a not reached)")
        return 0

    map_entries = ap.parse_responsibility_map(resp_map)
    spec_paths = ap.concept_spec_paths(cs.concept_source_dirs(feature))

    failures = []
    checked = 0
    for concept, origin, actions in parse_bindings(bindings):
        entry = map_entries.get(concept)
        if entry is None:
            failures.append(
                f"binding `{concept}` is not declared in the 01a responsibility "
                f"map")
            continue
        map_origin = (entry.origin or "").strip()
        if origin and map_origin and origin != map_origin:
            failures.append(
                f"binding `{concept}` says `{origin}` but the 01a map says "
                f"`{map_origin}`")
        if concept in spec_paths:
            declared = spec_actions(spec_paths[concept])
            for action in actions:
                checked += 1
                if action not in declared:
                    failures.append(
                        f"binding `{concept}` lists action `{action}`, which "
                        f"`{concept}` does not declare")

    if failures:
        print(f"FAIL  {len(failures)} concept-binding defect(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS  concept bindings agree with the 01a map ({checked} action(s) "
          f"resolved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
