#!/usr/bin/env python3
"""
verify_iterative_change_readiness.py - Gate: iterative changes must carry a
classification and artefact-impact matrix before implementation work proceeds.

Why this exists:
  CLAD R17 requires agents to classify iterative changes before modifying
  concept/sync specs or implementations. This script makes that rule
  deterministic: if the diff touches iterative-change scope, a structured
  change artefact must exist and be complete.

Usage:
  python3 quality-gate/verify_iterative_change_readiness.py \
    --feature features/UC-00-login \
    --base origin/main

  python3 quality-gate/verify_iterative_change_readiness.py \
    --feature features/UC-00-login \
    --change-file features/UC-00-login/_changes/lockout-threshold.md
"""

import argparse
import os
import re
import subprocess
import sys


CATEGORIES = {"presentation", "behavioural", "behavioral", "structural"}
PRODUCTION_CODE_ROW = "Production code"
ITERATIVE_PATTERNS = (
    re.compile(r"^features/UC-[^/]+/stages/02_concepts/output/.*\.concept\.md$"),
    re.compile(r"^features/UC-[^/]+/stages/03_syncs/output/.*\.sync\.md$"),
    re.compile(r"(^|/)(concepts|syncs)/.*\.(java|kt|scala|ts|js|py)$"),
)
IMPLEMENTATION_PATTERN = re.compile(r"(^|/)(concepts|syncs)/.*\.(java|kt|scala|ts|js|py)$")
REQUIRED_MATRIX_ROWS = (
    "Concept(s)",
    "Sync(s)",
    "SPEC slices",
    "Flow tests",
    "Concept tests",
    "Sync tests",
    PRODUCTION_CODE_ROW,
)


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


def in_iterative_scope(path):
    return any(pattern.search(path) for pattern in ITERATIVE_PATTERNS)


def in_implementation_scope(path):
    return IMPLEMENTATION_PATTERN.search(path) is not None


def discover_change_files(feature_root):
    changes_dir = os.path.join(feature_root, "_changes")
    if not os.path.isdir(changes_dir):
        return []
    return sorted(
        os.path.join(changes_dir, filename)
        for filename in os.listdir(changes_dir)
        if filename.endswith((".md", ".json"))
    )


def select_change_file(feature_root, explicit_path):
    if explicit_path:
        return explicit_path, []
    candidates = discover_change_files(feature_root)
    if len(candidates) == 1:
        return candidates[0], []
    if not candidates:
        return "", [(feature_root, "no iterative change artefact found; expected one under _changes/")]
    return "", [(feature_root, "multiple _changes artefacts found; pass --change-file explicitly")]


def field_value(text, label):
    match = re.search(rf"^[-*]?\s*\*\*{re.escape(label)}:\*\*\s*`?([^`\n]+)`?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def matrix_rows(text):
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[0] not in {"Artefact", "---"}:
            rows[cells[0]] = {"touched": cells[2].lower(), "how": cells[3]}
    return rows


def rederivation_steps(text):
    marker = "## Re-derivation order"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1]
    next_heading = re.search(r"^##\s+", section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    steps = []
    for line in section.splitlines():
        stripped = line.strip()
        prefix, separator, value = stripped.partition(".")
        if prefix.isdigit() and separator and value.strip() and "<stage>" not in value:
            steps.append(value.strip())
    return steps


def validate_change_file(path, implementation_touched):
    failures = []
    if not os.path.isfile(path):
        return [(path, "iterative change artefact not found")]
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    category = field_value(text, "Change category").lower()
    if category not in CATEGORIES:
        failures.append((path, "missing or invalid `Change category` field"))
    if not field_value(text, "Earliest re-entry stage"):
        failures.append((path, "missing `Earliest re-entry stage` field"))
    if "ITERATIVE_CHANGES.md" not in text:
        failures.append((path, "must cite methodology/core/ITERATIVE_CHANGES.md"))

    rows = matrix_rows(text)
    for row in REQUIRED_MATRIX_ROWS:
        if row not in rows:
            failures.append((path, f"artefact-impact matrix missing row: {row}"))
    touched_rows = [name for name, row in rows.items() if row["touched"].startswith("yes")]
    if not touched_rows:
        failures.append((path, "artefact-impact matrix marks no artefacts as touched"))
    if implementation_touched and PRODUCTION_CODE_ROW in rows and not rows[PRODUCTION_CODE_ROW]["touched"].startswith("yes"):
        failures.append((path, "diff touches implementation scope but Production code is not marked touched"))
    if not rederivation_steps(text):
        failures.append((path, "missing concrete Re-derivation order steps"))
    return failures


def main():
    parser = argparse.ArgumentParser(description="Verify iterative-change readiness artefact exists and is complete.")
    parser.add_argument("--feature", required=True, help="Feature root, e.g. features/UC-00-login")
    parser.add_argument("--change-file", default="", help="Path to the iterative change artefact")
    parser.add_argument("--base", default="origin/main", help="Base ref for git diff detection")
    parser.add_argument("--changed-files-file", default="", help="Test hook: newline-delimited changed file list")
    args = parser.parse_args()

    changed = changed_files(args.base, args.changed_files_file)
    touched_scope = [path for path in changed if in_iterative_scope(path)]
    implementation_touched = any(in_implementation_scope(path) for path in touched_scope)
    if not touched_scope:
        print("PASS  no iterative concept/sync spec or implementation changes detected")
        sys.exit(0)

    change_file, failures = select_change_file(args.feature, args.change_file)
    if change_file:
        failures.extend(validate_change_file(change_file, implementation_touched))

    if failures:
        print(f"FAIL: {len(failures)} iterative-change readiness violation(s):\n")
        for path, message in failures:
            print(f"  {path}\n    {message}\n")
        print("Open methodology/core/ITERATIVE_CHANGES.md and fill an artefact-impact matrix before proceeding.")
        sys.exit(1)

    print(f"PASS  iterative-change readiness recorded in {change_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()