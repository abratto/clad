#!/usr/bin/env python3
"""
verify_collection_coverage.py — Stage gate: collection responses carry
empty + multi-item (and repeated-key) fixtures.

Why this exists:
  Design-time gates verify structure, not cardinality. The conduit rebuild
  experiment twice reached Stage 05 with a collection defect no earlier gate
  could see: UC-07 (view comments) never exercised an empty thread or a
  multi-comment thread, and UC-12 (view feed) never exercised a page with a
  REPEATED key, so a per-article positional misalignment survived to runtime
  back-trace. This check makes the missing fixtures visible at Stage 04c, where
  the human already reviews the executable spec.

Rule:
  A feature whose chain tables / SPECs expose a COLLECTION response (a plural
  envelope key such as `articles`, `comments`, `tags`, `authors`, `following`,
  `flags`, or a `List<...>` completion field) must declare a
  `## Collection coverage` section in a markdown file under
  `04c_flow-tests/output/`. The section must name, at minimum:
    * `empty`        — the zero-item success case;
    * `multi-item`   — a case with at least two items;
    * `repeated-key` — a case where two positionally-aligned lists share a key
                       (or `n/a` with a one-line reason).
  The section is how the round-2 collection defects (UC-07/UC-12) are surfaced
  to the Gate-3 reviewer instead of hiding until Stage 05.

No retrofit:
  Features already closed (a `05_verify/output/trace.md` exists) are skipped, so
  the requirement is forward-only — the same no-retrofit policy as the T2
  test-continuity gate.

Usage:
  python3 verify_collection_coverage.py --feature features/UC-XX-<slug> [--advisory]

Exit: 0 pass/warn/skip, 1 fail.
"""

import argparse
import os
import re
import sys

COLLECTION_KEYS = (
    "articles", "comments", "tags", "taglists", "authors", "profiles",
    "following", "flags", "favoritescounts", "articleids", "commentids",
    "authorusernames", "summaries",
)

SECTION_RE = re.compile(r"^##\s+Collection coverage\s*$(.*?)(?=^##\s|\Z)",
                        re.MULTILINE | re.DOTALL)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def markdown_files(directory):
    if not os.path.isdir(directory):
        return []
    return [os.path.join(directory, name)
            for name in sorted(os.listdir(directory))
            if name.endswith(".md")]


def collection_signal(feature_root):
    """Return (is_collection_shaped, evidence) for the feature.

    A feature is collection-shaped when a chain table names a plural collection
    envelope key or a SPEC declares a `List<...>` completion field.
    """
    chain_dir = os.path.join(feature_root, "stages", "01b_chain-table", "output")
    spec_dir = os.path.join(feature_root, "stages",
                            "04_implement", "04b_spec", "output")

    blob = ""
    for path in markdown_files(chain_dir):
        blob += read(path)

    for path in markdown_files(spec_dir):
        text = read(path)
        if "List<" in text or "List&lt;" in text:
            return True, "%s declares a List<...> field" % os.path.basename(path)
        blob += text

    low = blob.lower()
    for key in COLLECTION_KEYS:
        if re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", low):
            return True, "chain/SPEC names the collection key %r" % key
    return False, ""


def declared_coverage(flow_dir):
    """Return (file, body) of the first `## Collection coverage` section."""
    for path in markdown_files(flow_dir):
        match = SECTION_RE.search(read(path))
        if match:
            return path, match.group(1)
    return None, ""


def main():
    parser = argparse.ArgumentParser(
        description="Verify collection responses declare empty/multi-item/repeated-key fixtures"
    )
    parser.add_argument("--feature", required=True, help="Feature root, e.g. features/UC-XX-<slug>")
    parser.add_argument("--advisory", action="store_true",
                        help="Report a failure as a warning (exit 0) instead of failing")
    args = parser.parse_args()

    feature_root = args.feature
    if not os.path.isdir(feature_root):
        print("FAIL  feature root not found: %s" % feature_root)
        return 1

    # No retrofit: a closed feature (has a Stage-05 trace) is grandfathered.
    if os.path.isfile(os.path.join(feature_root, "stages", "05_verify",
                                   "output", "trace.md")):
        print("SKIP  feature is closed (no retrofit)")
        return 0

    shaped, evidence = collection_signal(feature_root)
    if not shaped:
        print("SKIP  no collection response declared")
        return 0

    flow_dir = os.path.join(feature_root, "stages", "04_implement",
                            "04c_flow-tests", "output")
    if not markdown_files(flow_dir):
        print("SKIP  no 04c flow-test output yet")
        return 0

    path, body = declared_coverage(flow_dir)
    failures = []
    if path is None:
        failures.append("no `## Collection coverage` section under "
                        "04c_flow-tests/output/ (collection signal: %s)" % evidence)
    else:
        low = body.lower()
        if "empty" not in low:
            failures.append("`## Collection coverage` does not name the empty case")
        if not re.search(r"multi[- ]?item|\bmulti\b", low):
            failures.append("`## Collection coverage` does not name the multi-item case")
        if not re.search(r"repeat", low):
            failures.append("`## Collection coverage` does not name the repeated-key "
                            "case (or 'n/a' with a reason)")

    if failures:
        label = "WARN" if args.advisory else "FAIL"
        print("%s  collection coverage incomplete for a collection-shaped feature" % label)
        for failure in failures:
            print("  - %s" % failure)
        return 0 if args.advisory else 1

    print("PASS  collection coverage declared (empty, multi-item, repeated-key)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
