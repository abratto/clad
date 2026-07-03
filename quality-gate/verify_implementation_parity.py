#!/usr/bin/env python3
"""
verify_implementation_parity.py - Gate: every sync/concept implementation
class has a corresponding spec artefact.

Why this exists:
  CLAD R17 requires that every change to a sync or concept class is
  accompanied by an update to the corresponding stage artefact. This
  script mechanises the forward direction: for each implementation class
  found, it checks that a spec file exists somewhere in the features tree.
  A class without a spec indicates R17 was skipped.

Checks:
  1. Every *.java (or *.kt, *.scala) file in --sync-impl-dir has a
     corresponding <ClassName>.sync.md in --features-dir (searched
     recursively under stages/03_syncs/output/).
  2. Every *.java (or *.kt, *.scala) file in --concept-impl-dir has a
     corresponding spec file in --features-dir (searched recursively
     under stages/02_concepts/output/). The match is: strip a trailing
     'Concept' suffix from the class name, then look for a file whose
     stem (before .concept.md) case-insensitively equals that stripped
     name.

Directories are optional: if --sync-impl-dir or --concept-impl-dir is
not provided (or does not exist), that check is skipped with a warning.

Exit 0 if all checks pass. Exit 1 with a list of missing specs.

Usage:
  python3 verify_implementation_parity.py \
    --sync-impl-dir   app/backend/src/main/java/org/example/syncs \
    --concept-impl-dir app/backend/src/main/java/org/example/concepts \
    --features-dir    features/
"""

import argparse
import os
import sys

IMPL_EXTENSIONS = {".java", ".kt", ".scala"}


def collect_class_names(directory):
    """Return a list of (filename, class_name) for all implementation files
    found recursively under directory."""
    results = []
    if not os.path.isdir(directory):
        return results
    for root, _, files in os.walk(directory):
        for filename in files:
            stem, ext = os.path.splitext(filename)
            if ext in IMPL_EXTENSIONS:
                results.append((os.path.join(root, filename), stem))
    return results


def collect_spec_stems(features_dir, sub_path, suffix):
    """Collect the set of spec file stems (lower-cased, suffix stripped)
    found recursively under features_dir/*/stages/<sub_path>/.
    suffix is e.g. '.sync.md' or '.concept.md'."""
    stems = set()
    if not os.path.isdir(features_dir):
        return stems
    for root, _, files in os.walk(features_dir):
        if sub_path not in root:
            continue
        for filename in files:
            if filename.endswith(suffix):
                stem = filename[: -len(suffix)]
                stems.add(stem.lower())
    return stems


def check_syncs(sync_impl_dir, features_dir):
    """Check every sync implementation class has a *.sync.md spec.
    Returns list of (path, message) failure tuples."""
    failures = []
    if not os.path.isdir(sync_impl_dir):
        print(f"  [SKIP] sync-impl-dir not found: {sync_impl_dir}", file=sys.stderr)
        return failures

    spec_stems = collect_spec_stems(features_dir, "03_syncs/output", ".sync.md")
    for path, class_name in collect_class_names(sync_impl_dir):
        if class_name.lower() not in spec_stems:
            failures.append(
                (path, f"No *.sync.md found for class '{class_name}' "
                       f"(searched recursively under {features_dir})")
            )
    return failures


def strip_concept_suffix(class_name):
    """Strip a trailing 'Concept' suffix (case-insensitive) from class_name."""
    if class_name.lower().endswith("concept"):
        return class_name[: -len("concept")]
    return class_name


def check_concepts(concept_impl_dir, features_dir):
    """Check every concept implementation class has a *.concept.md spec.
    Returns list of (path, message) failure tuples."""
    failures = []
    if not os.path.isdir(concept_impl_dir):
        print(f"  [SKIP] concept-impl-dir not found: {concept_impl_dir}", file=sys.stderr)
        return failures

    spec_stems = collect_spec_stems(features_dir, "02_concepts/output", ".concept.md")
    for path, class_name in collect_class_names(concept_impl_dir):
        stripped = strip_concept_suffix(class_name)
        if stripped.lower() not in spec_stems:
            failures.append(
                (path, f"No *.concept.md found for class '{class_name}' "
                       f"(tried stem '{stripped}', searched recursively under {features_dir})")
            )
    return failures


def main():
    parser = argparse.ArgumentParser(
        description="Verify every sync/concept implementation class has a spec artefact."
    )
    parser.add_argument(
        "--sync-impl-dir",
        default="",
        help="Directory containing sync implementation classes (searched recursively).",
    )
    parser.add_argument(
        "--concept-impl-dir",
        default="",
        help="Directory containing concept implementation classes (searched recursively).",
    )
    parser.add_argument(
        "--features-dir",
        default="features",
        help="Root of the features/ tree (default: features/).",
    )
    args = parser.parse_args()

    failures = []

    if args.sync_impl_dir:
        failures.extend(check_syncs(args.sync_impl_dir, args.features_dir))

    if args.concept_impl_dir:
        failures.extend(check_concepts(args.concept_impl_dir, args.features_dir))

    if not args.sync_impl_dir and not args.concept_impl_dir:
        print(
            "ERROR: at least one of --sync-impl-dir or --concept-impl-dir is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    if failures:
        print(f"FAIL: {len(failures)} implementation parity violation(s):\n")
        for path, message in sorted(failures):
            print(f"  {path}\n    {message}\n")
        print(
            "Each violation means R17 was skipped: an implementation class was\n"
            "added or modified without a corresponding stage artefact update.\n"
            "Open methodology/core/ITERATIVE_CHANGES.md, classify the change,\n"
            "and add the missing *.sync.md or *.concept.md before committing."
        )
        sys.exit(1)

    total = 0
    if args.sync_impl_dir and os.path.isdir(args.sync_impl_dir):
        total += len(collect_class_names(args.sync_impl_dir))
    if args.concept_impl_dir and os.path.isdir(args.concept_impl_dir):
        total += len(collect_class_names(args.concept_impl_dir))
    print(f"OK: {total} implementation class(es) each have a spec artefact.")
    sys.exit(0)


if __name__ == "__main__":
    main()