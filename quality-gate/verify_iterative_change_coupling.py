#!/usr/bin/env python3
"""
verify_iterative_change_coupling.py - Gate: implementation and stage artefacts
must move together for iterative concept/sync changes.

Why this exists:
  A Java concept or sync class can drift from its CLAD contract if only the
  implementation side is touched. This script reads the diff and fails when a
  concept/sync implementation changes without its corresponding stage artefact.

  The rule (R17) is about *iterative* change: an implementation that already
  had an approved spec is modified without re-deriving that spec. It therefore
  fires only when BOTH sides already exist at the base revision. A greenfield
  first addition (class and spec both new on this branch) and a same-diff
  spec+impl pair are NOT coupling violations — requiring a spec that the
  per-gate commit flow has not yet committed was the v0.13.0 experiment's
  blocker (D31).

  Import/package-only changes (e.g. a package rename that rewrites `import`
  lines without touching behaviour) are Presentation changes under R17 and do
  not invalidate the Stage 02/03 artefacts, so they are skipped.

  Bootstrap concepts (`Web`, `Grpc`, `Cli`, `Stream`) are governed by the shared
  bootstrap-concept docs, never by a per-feature `02_concepts` spec, so their
  implementations are exempt (D29).

Usage:
  python3 quality-gate/verify_iterative_change_coupling.py --base origin/main
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


CONCEPT_IMPL_RE = re.compile(r"(^|/)concepts/([^/]+)/([^/]+)\.(java|kt|scala)$")
SYNC_IMPL_RE = re.compile(r"(^|/)syncs/([^/]+)\.(java|kt|scala)$")
CONCEPT_SPEC_RE = re.compile(r"^features/UC-[^/]+/stages/02_concepts/output/([^/]+)\.concept\.md$")
# The canonical corpus spec (maintenance change `system-scope-concept-vocabulary`)
# also satisfies concept/spec coupling, so an implementation change paired with a
# corpus spec edit is accepted.
CORPUS_SPEC_RE = re.compile(r"^features/_system/concepts/([^/]+)\.concept\.md$")
SYNC_SPEC_RE = re.compile(r"^features/UC-[^/]+/stages/03_syncs/output/([^/]+)\.sync\.md$")

# A diff line is a "presentation-only" line if it declares a package or import.
IMPORT_PACKAGE_LINE = re.compile(r"^(import\s+|package\s+)")

# Bootstrap concepts own the transport boundary and are governed by the shared
# bootstrap-concept docs; they have no per-feature 02_concepts spec, so R17
# coupling cannot and must not demand one (D29).
BOOTSTRAP_CONCEPTS = {"web", "grpc", "cli", "stream"}

# Classes under `concepts/`/`syncs/` that are NOT business concept/sync
# implementations: tests, fixtures, rule-pack aggregators, registries, and
# schema helpers. Matching them made a greenfield implementation commit produce
# 18 false coupling violations (D30).
NON_IMPL_CLASS_SUFFIXES = (
    "test", "tests", "fixture", "fixtures",
    "syncrules", "rules", "registry", "registries", "schemas",
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
    # Committed-on-branch + staged only. The unstaged working tree is NOT part
    # of a commit, so including it blocked the mandated per-gate commit whenever
    # post-gate implementation was in progress (D42).
    names = set(run_git_names(["git", "diff", "--name-only", f"{base}...HEAD"]))
    names.update(run_git_names(["git", "diff", "--name-only", "--cached"]))
    return sorted(names)


def diff_text_for(path, base):
    """Combined unified diff (added/removed lines) for a path across the same
    surfaces used by changed_files()."""
    surfaces = [
        ["git", "diff", "--unified=0", f"{base}...HEAD", "--", path],
        ["git", "diff", "--unified=0", "--cached", "--", path],
    ]
    parts = []
    for surface in surfaces:
        parts.extend(run_git_names(surface))
    return "\n".join(parts)


def is_import_or_package_only_diff(diff_text):
    """True when a unified diff changes only import/package lines (a pure
    package move or import re-write with no behavioural change)."""
    changed = []
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") or line.startswith("-"):
            content = line[1:].strip()
            if content:
                changed.append(content)
    if not changed:
        return True
    return all(IMPORT_PACKAGE_LINE.match(line) for line in changed)


def is_import_or_package_only(path, base):
    return is_import_or_package_only_diff(diff_text_for(path, base))


def exists_at_base(path, base):
    """True when `path` exists in the base revision (git object exists)."""
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{base}:{path}"],
        check=False, capture_output=True, text=True)
    return result.returncode == 0


def _normalise(path):
    return path.replace("\\", "/")


def is_production_impl_path(path):
    """True for a source file under a `src/main/` tree (never `src/test/`).

    CLAD profiles place concept/sync implementations under Maven `src/main/java`
    (or equivalent `src/main/<lang>`); tests, fixtures and harnesses live under
    `src/test`. The bare `concepts/`/`syncs/` regex matched both (D30)."""
    norm = _normalise(path)
    if "/src/test/" in norm or norm.startswith("src/test/"):
        return False
    return "/src/main/" in norm or norm.startswith("src/main/")


def is_non_impl_class(class_name):
    return class_name.lower().endswith(NON_IMPL_CLASS_SUFFIXES)


def concept_name_from_class(class_name):
    if class_name.lower().endswith("concept"):
        return class_name[: -len("Concept")]
    return class_name


def changed_concept_impls(paths, import_only_filter=None, is_new=None):
    concepts = set()
    for path in paths:
        match = CONCEPT_IMPL_RE.search(path)
        if not match:
            continue
        if not is_production_impl_path(path):
            continue
        if is_new is not None and is_new(path):
            # Greenfield addition: no spec existed to re-derive (D31).
            continue
        if import_only_filter is not None and import_only_filter(path):
            continue
        package_name = match.group(2)
        class_name = os.path.splitext(match.group(3))[0]
        if is_non_impl_class(class_name):
            continue
        name = concept_name_from_class(class_name) or package_name
        if name.strip().lower() in BOOTSTRAP_CONCEPTS:
            continue
        concepts.add(name)
    return concepts


def changed_sync_impls(paths, import_only_filter=None, is_new=None):
    syncs = set()
    for path in paths:
        match = SYNC_IMPL_RE.search(path)
        if not match:
            continue
        if not is_production_impl_path(path):
            continue
        if is_new is not None and is_new(path):
            continue
        if import_only_filter is not None and import_only_filter(path):
            continue
        class_name = os.path.splitext(match.group(2))[0]
        if is_non_impl_class(class_name):
            continue
        syncs.add(class_name)
    return syncs


def changed_concept_specs(paths):
    return {
        match.group(1)
        for path in paths
        if (match := (CONCEPT_SPEC_RE.match(path) or CORPUS_SPEC_RE.match(path)))
    }


def changed_sync_specs(paths):
    return {match.group(1) for path in paths if (match := SYNC_SPEC_RE.match(path))}


def lower_set(values):
    return {value.lower() for value in values}


def missing_matches(impl_names, spec_names):
    spec_lookup = lower_set(spec_names)
    return sorted(name for name in impl_names if name.lower() not in spec_lookup)


def has_active_maintenance_record():
    """True when an active maintenance/<change-name>.md governs the current work.

    R17 (iterative-change coupling) and R20 (platform maintenance) are separate
    governance paths. A maintenance change may add or re-realize concept/sync
    implementations in a new profile without re-deriving their already-approved
    specs; that coupling is governed by the maintenance record's test matrix,
    not this gate.
    """
    maintenance_dir = Path(__file__).resolve().parent.parent / "maintenance"
    if not maintenance_dir.is_dir():
        return False
    status_re = re.compile(r"^- \*\*Status:\*\* `?active`?\s*$", re.MULTILINE)
    for path in maintenance_dir.glob("*.md"):
        if status_re.search(path.read_text(encoding="utf-8")):
            return True
    return False


def has_active_iterative_change():
    """True when any feature carries an active `_changes/` record.

    Re-deriving a concept/sync spec+impl is an ITERATIVE change (R17). During
    ordinary feature-stage work there is no active change record — the feature's
    own spec and impl are being authored across the gate commits — so coupling
    does not apply, and requiring the spec in the same commit as a first or
    extension implementation contradicted the per-gate commit flow (experiment
    defect D31). Readiness (`verify_iterative_change_readiness.py`) still forces
    a `_changes/` record for any implementation edit outside new stage work, so
    this gate cannot be bypassed for a genuine iterative change.
    """
    features_dir = Path(__file__).resolve().parent.parent / "features"
    if not features_dir.is_dir():
        return False
    status_re = re.compile(r"^- \*\*Status:\*\*\s*`?active`?\s*$", re.MULTILINE)
    for change in features_dir.glob("UC-*/_changes/*.md"):
        try:
            if status_re.search(change.read_text(encoding="utf-8")):
                return True
        except OSError:
            continue
    return False


def main():
    parser = argparse.ArgumentParser(description="Verify iterative implementation/spec coupling in the diff.")
    parser.add_argument("--base", default="origin/main", help="Base ref for git diff detection")
    parser.add_argument("--changed-files-file", default="", help="Test hook: newline-delimited changed file list")
    args = parser.parse_args()

    if has_active_maintenance_record():
        print("PASS  maintenance-governed change (R20); iterative-change coupling (R17) not applicable")
        sys.exit(0)

    if not has_active_iterative_change():
        print("PASS  no active iterative change (R17 coupling not applicable; "
              "feature-stage work is governed by the readiness/sequence gates)")
        sys.exit(0)

    changed = changed_files(args.base, args.changed_files_file)

    # In git mode, ignore pure package/import renames: they are Presentation
    # changes (R17) and do not invalidate the Stage 02/03 artefacts. The test
    # hook (--changed-files-file) has no git diff to inspect, so it is exempt.
    import_only_filter = None
    is_new = None
    if not args.changed_files_file:
        import_only_filter = lambda path: is_import_or_package_only(path, args.base)
        is_new = lambda path: not exists_at_base(path, args.base)

    concept_impls = changed_concept_impls(changed, import_only_filter, is_new)
    sync_impls = changed_sync_impls(changed, import_only_filter, is_new)
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
