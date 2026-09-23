#!/usr/bin/env python3
"""
verify_reference_integrity.py — a rename must not leave a dangling reference.

Why this exists:
  Renaming a sync or concept is mechanical for the artefact itself, but its tail
  is not: cards, derivation maps, traces, the `.feature`, and the README cite the
  artefact by filename, and the Java rule / test class is named after it. The
  route-scoped-pinned-names change touched ~25 syncs across two repos; the tail
  was found by hand. This check catches it mechanically.

Checks (per feature; `_changes/` history and bootstrap concepts are exempt):
  * A backticked `<Name>.sync.md` reference must resolve to a real sync spec in
    the feature's `03_syncs/output/`.
  * A backticked `<Name>.concept.md` / `.contract.md` / `.data-model.md`
    reference must resolve to the feature's output or the canonical corpus.
  * With `--sync-impl-dir`, every Java `rule("Name")` / `SyncRule.of("Name", …)`
    must match a real sync stem in some feature (an orphan rule is a rename
    tail).

Usage:
  python3 verify_reference_integrity.py --features-dir features \
      [--sync-impl-dir <impl dir>]

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import re
import sys

# `Name.<kind>.md` inside backticks.
REF = re.compile(r"`([A-Za-z0-9_]+)\.(sync|concept|contract|data-model)\.md`")
RULE_NAME = re.compile(r'(?:SyncRule\.ofJoin|SyncRule\.of|rule)\(\s*"(\w+)"')
BOOTSTRAP = {"Web", "Grpc", "Stream", "Cli"}
SKIP_DIRS = {"_changes", "__pycache__", "target"}


def feature_dirs(features_dir):
    if not os.path.isdir(features_dir):
        return []
    return [os.path.join(features_dir, n) for n in sorted(os.listdir(features_dir))
            if n.startswith("UC-") and os.path.isdir(os.path.join(features_dir, n))]


def stems(directory, suffix):
    if not os.path.isdir(directory):
        return set()
    return {f[: -len(suffix)] for f in os.listdir(directory) if f.endswith(suffix)}


def available(feature_root, corpus):
    return {
        "sync": stems(os.path.join(feature_root, "stages/03_syncs/output"), ".sync.md"),
        "concept": stems(os.path.join(feature_root, "stages/02_concepts/output"),
                         ".concept.md") | corpus["concept"],
        "contract": stems(
            os.path.join(feature_root, "stages/04_implement/04b_contract/output"),
            ".contract.md") | corpus["contract"],
        "data-model": stems(
            os.path.join(feature_root, "stages/03b-data-model/output"),
            ".data-model.md") | corpus["data-model"],
    }


def markdown_files(feature_root):
    for dirpath, dirs, files in os.walk(feature_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if name.endswith(".md") or name.endswith(".feature"):
                yield os.path.join(dirpath, name)


def java_rule_names(sync_impl_dir):
    if not sync_impl_dir or not os.path.isdir(sync_impl_dir):
        return []
    names = []
    for dirpath, dirs, files in os.walk(sync_impl_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith(".java"):
                continue
            with open(os.path.join(dirpath, name), encoding="utf-8",
                      errors="replace") as handle:
                names += RULE_NAME.findall(handle.read())
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename-tail reference check")
    parser.add_argument("--features-dir", default="features")
    parser.add_argument("--sync-impl-dir", default="")
    args = parser.parse_args()

    features_dir = os.path.abspath(args.features_dir)
    features = feature_dirs(features_dir)
    if not features:
        print(f"SKIP  no features under {features_dir}")
        return 0

    corpus = {
        "concept": stems(os.path.join(features_dir, "_system/concepts"), ".concept.md"),
        "contract": stems(os.path.join(features_dir, "_system/concepts"), ".contract.md"),
        "data-model": stems(os.path.join(features_dir, "_system/concepts"), ".data-model.md"),
    }

    failures = []
    checked = 0
    all_sync_stems = set()
    for feature in features:
        have = available(feature, corpus)
        all_sync_stems |= have["sync"]
        rel = os.path.basename(feature)
        for path in markdown_files(feature):
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            for name, kind in REF.findall(text):
                if kind in ("concept", "contract", "data-model") and name in BOOTSTRAP:
                    continue
                checked += 1
                if name not in have[kind]:
                    failures.append(
                        f"{rel}/{os.path.relpath(path, feature)}: `{name}.{kind}.md` "
                        f"resolves to no {kind} artefact")

    if args.sync_impl_dir:
        for name in sorted(set(java_rule_names(args.sync_impl_dir))):
            checked += 1
            if name not in all_sync_stems:
                failures.append(
                    f"{args.sync_impl_dir}: `rule(\"{name}\")` matches no sync spec "
                    f"in any feature (orphan rule / rename tail)")

    if failures:
        print(f"FAIL  {len(failures)} dangling reference(s):")
        for failure in failures[:20]:
            print(f"  - {failure}")
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
        return 1
    print(f"PASS  {checked} reference(s) resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
