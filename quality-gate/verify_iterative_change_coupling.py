#!/usr/bin/env python3
"""
verify_iterative_change_coupling.py - Gate: implementation and stage artefacts
must move together for iterative concept/sync changes.

Why this exists:
  A Java concept or sync class can drift from its CLAD contract if only the
  implementation side is touched. This script reads the diff and fails when a
  concept/sync implementation changes without its corresponding stage artefact.

Usage:
  python3 quality-gate/verify_iterative_change_coupling.py --base origin/main
"""

import argparse
import os
import re
import subprocess
import sys


CONCEPT_IMPL_RE = re.compile(r"(^|/)concepts/([^/]+)/([^/]+)\.(java|kt|scala)$")
SYNC_IMPL_RE = re.compile(r"(^|/)syncs/([^/]+)\.(java|kt|scala)$")
CONCEPT_SPEC_RE = re.compile(r"^features/UC-[^/]+/stages/02_concepts/output/([^/]+)\.concept\.md$")
SYNC_SPEC_RE = re.compile(r"^features/UC-[^/]+/stages/03_syncs/output/([^/]+)\.sync\.md$")


def run_git_names(args):
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(base, changed_files_file):
    if changed_files_file:
        with open(changed_files_file, encoding="utf-8") as handle:
            return sorted({line.strip() for line in handle if line.strip()})
    names = set(run_git_names(["git", "diff", "--name-only", f"{base}...HEAD"]))
    names.update(run_git_names(["git", "diff", "--name-only", "--cached"]))
    names.update(run_git_names(["git", "diff", "--name-only"]))
    return sorted(names)


def concept_name_from_class(class_name):
    if class_name.lower().endswith("concept"):
        return class_name[: -len("Concept")]
    return class_name


def changed_concept_impls(paths):
    concepts = set()
    for path in paths:
        match = CONCEPT_IMPL_RE.search(path)
        if match:
            package_name = match.group(2)
            class_name = os.path.splitext(match.group(3))[0]
            concepts.add(concept_name_from_class(class_name) or package_name)
    return concepts


def changed_sync_impls(paths):
    syncs = set()
    for path in paths:
        match = SYNC_IMPL_RE.search(path)
        if match:
            syncs.add(os.path.splitext(match.group(2))[0])
    return syncs


def changed_concept_specs(paths):
    return {match.group(1) for path in paths if (match := CONCEPT_SPEC_RE.match(path))}


def changed_sync_specs(paths):
    return {match.group(1) for path in paths if (match := SYNC_SPEC_RE.match(path))}


def lower_set(values):
    return {value.lower() for value in values}


def missing_matches(impl_names, spec_names):
    spec_lookup = lower_set(spec_names)
    return sorted(name for name in impl_names if name.lower() not in spec_lookup)


def main():
    parser = argparse.ArgumentParser(description="Verify iterative implementation/spec coupling in the diff.")
    parser.add_argument("--base", default="origin/main", help="Base ref for git diff detection")
    parser.add_argument("--changed-files-file", default="", help="Test hook: newline-delimited changed file list")
    args = parser.parse_args()

    changed = changed_files(args.base, args.changed_files_file)
    concept_impls = changed_concept_impls(changed)
    sync_impls = changed_sync_impls(changed)
    concept_specs = changed_concept_specs(changed)
    sync_specs = changed_sync_specs(changed)

    failures = []
    for name in missing_matches(concept_impls, concept_specs):
        failures.append((name, "concept implementation changed without matching 02_concepts/output/*.concept.md"))
    for name in missing_matches(sync_impls, sync_specs):
        failures.append((name, "sync implementation changed without matching 03_syncs/output/*.sync.md"))

    if failures:
        print(f"FAIL: {len(failures)} iterative-change coupling violation(s):\n")
        for name, message in failures:
            print(f"  {name}\n    {message}\n")
        print("Re-enter the earliest owning CLAD stage and commit the stage artefact with the implementation change.")
        sys.exit(1)

    print("PASS  iterative implementation/spec coupling is satisfied")
    sys.exit(0)


if __name__ == "__main__":
    main()