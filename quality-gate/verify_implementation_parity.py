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
  2. Every sync spec filename, `sync <Name>` header, and implementation
      class name follows the mechanical compressed-rule grammar:
      When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>].
  3. Every *.java (or *.kt, *.scala) file in --concept-impl-dir has a
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
import re
import sys

IMPL_EXTENSIONS = {".java", ".kt", ".scala"}
SYNC_DECL_RE = re.compile(r"^sync\s+(\w+)\s*$", re.MULTILINE)
RULE_BLOCK_RE = re.compile(r"## Rule\s*(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
WHEN_RE = re.compile(r"(\w+)/(\w+)\s*:\s*\[[^\]]*\]\s*=>\s*\[([^\]]*)\]", re.DOTALL)
THEN_RE = re.compile(r"(\w+)/(\w+)\s*:")


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
    """Collect spec file stems mapped to paths (lower-cased, suffix stripped)
    found recursively under features_dir/*/stages/<sub_path>/.
    suffix is e.g. '.sync.md' or '.concept.md'."""
    stems = {}
    if not os.path.isdir(features_dir):
        return stems
    for root, _, files in os.walk(features_dir):
        if sub_path not in root:
            continue
        for filename in files:
            if filename.endswith(suffix):
                stem = filename[: -len(suffix)]
                stems[stem.lower()] = os.path.join(root, filename)
    return stems


def pascal_token(raw):
    """Convert a CLAD signature token to PascalCase for sync names."""
    token = raw.strip().strip("`").strip('"').strip("'")
    token = token.lstrip("?")
    parts = []
    for chunk in re.split(r"[^A-Za-z0-9]+", token):
        if not chunk:
            continue
        parts.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", chunk))
    return "".join(part[:1].upper() + part[1:].lower() for part in parts)


def lower_camel(name):
    return name[:1].lower() + name[1:] if name else name


def feature_scope_from_path(path):
    parts = os.path.normpath(path).split(os.sep)
    if "features" not in parts:
        return ""
    index = parts.index("features")
    if index + 1 >= len(parts):
        return ""
    feature = parts[index + 1]
    match = re.match(r"UC-\d+-(.+)", feature)
    return pascal_token(match.group(1) if match else feature)


def first_completion_token(completion):
    for raw_part in re.split(r"[;,]", completion):
        part = raw_part.strip()
        if not part:
            continue
        if ":" in part:
            _, value = part.split(":", 1)
            value = value.strip()
            if value.startswith('"') or value.startswith("'"):
                return pascal_token(value)
            return pascal_token(part.split(":", 1)[0])
        return pascal_token(part)
    return ""


def expected_sync_names(path, text):
    rule_match = RULE_BLOCK_RE.search(text)
    if not rule_match:
        return []
    rule = rule_match.group(1)
    when_match = WHEN_RE.search(rule)
    then_match = THEN_RE.search(rule[when_match.end():] if when_match else rule)
    if not when_match or not then_match:
        return []

    when_concept, when_action, completion = when_match.groups()
    then_concept, then_action = then_match.groups()
    base = (
        "When"
        + pascal_token(when_concept)
        + pascal_token(when_action)
        + first_completion_token(completion)
        + "Then"
        + pascal_token(then_concept)
        + pascal_token(then_action)
    )
    scope = feature_scope_from_path(path)
    names = [base]
    if scope:
        names.append(base + "For" + scope)
    return names


def collect_sync_specs(features_dir):
    specs = {}
    failures = []
    for _, path in collect_spec_stems(features_dir, "03_syncs/output", ".sync.md").items():
        stem = os.path.basename(path)[: -len(".sync.md")]
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        decl_match = SYNC_DECL_RE.search(text)
        if not decl_match:
            failures.append((path, "missing `sync <Name>` declaration"))
            continue
        declared = decl_match.group(1)
        if declared != stem:
            failures.append((path, f"filename stem '{stem}' does not match sync declaration '{declared}'"))
        expected = expected_sync_names(path, text)
        if not expected:
            failures.append((path, "could not derive mechanical When...Then sync name from ## Rule"))
            continue
        if stem not in expected:
            failures.append(
                (path, f"sync name '{stem}' does not match derived name; expected one of: {', '.join(expected)}")
            )
        specs[stem.lower()] = {"path": path, "declared": declared, "expected": expected}
    return specs, failures


def check_syncs(sync_impl_dir, features_dir):
    """Check every sync implementation class has a *.sync.md spec.
    Returns list of (path, message) failure tuples."""
    failures = []
    if not os.path.isdir(sync_impl_dir):
        print(f"  [SKIP] sync-impl-dir not found: {sync_impl_dir}", file=sys.stderr)
        return failures

    sync_specs, spec_failures = collect_sync_specs(features_dir)
    failures.extend(spec_failures)
    for path, class_name in collect_class_names(sync_impl_dir):
        sync_spec = sync_specs.get(class_name.lower())
        if not sync_spec:
            failures.append(
                (path, f"No *.sync.md found for class '{class_name}' "
                       f"(searched recursively under {features_dir})")
            )
            continue
        if class_name not in sync_spec["expected"]:
            failures.append(
                (path, f"sync class '{class_name}' does not match mechanical name from "
                       f"{sync_spec['path']} (expected one of: {', '.join(sync_spec['expected'])})")
            )
        expected_runtime = lower_camel(class_name)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        if f'return "{expected_runtime}"' not in text:
            failures.append(
                (path, f"syncName() must return lower camel case '{expected_runtime}'")
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
            "Each violation means R17 was skipped or the sync naming rule was\n"
            "not followed: implementation and stage artefacts no longer lower\n"
            "mechanically from the same CLAD contract.\n"
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