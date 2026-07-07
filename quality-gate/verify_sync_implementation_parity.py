#!/usr/bin/env python3
"""
verify_sync_implementation_parity.py - Gate: every Stage 03 sync spec has
a corresponding SyncAgent implementation class.

Why this exists:
  Stage 03 owns declarative *.sync.md contracts. Stage 04e-green must lower
  each approved sync into one executable SyncAgent subclass. A missing Java
  class leaves a gap that implementation-to-spec parity checks cannot catch,
  because those checks start from files that already exist.

Checks:
  1. Every *.sync.md under --sync-dir or --features-dir has a Sync Contract
     Matrix row with parseable when/then signatures.
  2. A matching class named <SyncName> exists under --sync-impl-dir.
  3. The class is annotated @Singleton and extends SyncAgent.
  4. With --strict-trigger, the class exposes matching trigger evidence,
      preferably through @SyncMetadata(triggeredBy = "Concept/action[OUTCOME]")
      and otherwise through trigger()/whereClause() source text.

Usage:
  python3 quality-gate/verify_sync_implementation_parity.py \
    --sync-dir features/UC-00-login/stages/03_syncs/output \
    --sync-impl-dir reference-impl/java-micronaut-jena/src/main/java/com/example/app/syncs

  python3 quality-gate/verify_sync_implementation_parity.py \
    --features-dir features \
        --sync-impl-dir app/backend/src/main/java/com/example/app/syncs

    Add --strict-trigger for profiles whose runtime vocabulary mirrors Stage 03
    concept/action/outcome tokens exactly.
"""

import argparse
import os
import re
import sys


IMPL_EXTENSIONS = {".java"}
SYNC_SUFFIX = ".sync.md"
SYNC_DECL_RE = re.compile(r"^sync\s+(\w+)\s*$", re.MULTILINE)
CLASS_RE = re.compile(r"\bclass\s+(\w+)\s+extends\s+SyncAgent\b")
METADATA_TRIGGER_RE = re.compile(r"triggeredBy\s*=\s*\"(\w+)/(\w+)\[([^\]]+)\]\"")
METADATA_FIRES_RE = re.compile(r"fires\s*=\s*\"(\w+)/(\w+)\[([^\]]+)\]\"")
SYNC_TRIGGER_RE = re.compile(
    r"new\s+SyncTrigger\s*\(\s*([A-Za-z0-9_.$]+)\s*,\s*\"([^\"]+)\""
)
OUTCOME_LITERAL_RE = re.compile(r":outcome\s+\"([^\"]+)\"")


def normalize_token(raw):
    return re.sub(r"[^a-z0-9]", "", raw.strip().lower())


def first_completion_token(completion):
    for raw_part in re.split(r"[;,]", completion):
        part = raw_part.strip().strip("`")
        if not part:
            continue
        if ":" in part:
            name, value = part.split(":", 1)
            value = value.strip()
            if value.startswith(('"', "'")):
                return value.strip('"\'')
            return name.strip()
        return part
    return ""


def parse_concept_action(raw):
    head = raw.strip().strip("`").split(":", 1)[0].strip()
    if "/" not in head:
        return None
    concept, action = head.split("/", 1)
    concept = concept.strip()
    action = action.strip()
    if not concept or not action:
        return None
    return concept, action


def parse_when_signature(signature):
    if "=>" not in signature:
        return None
    left, right = signature.split("=>", 1)
    concept_action = parse_concept_action(left)
    if concept_action is None or "[" not in right or "]" not in right:
        return None
    completion = right.split("[", 1)[1].split("]", 1)[0]
    return (*concept_action, first_completion_token(completion))


def parse_then_signature(signature):
    return parse_concept_action(signature)


def split_table_row(line):
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return [cell.strip().strip("`") for cell in cells]


def is_separator_row(cells):
    return all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells if cell)


def sync_files_in_dir(sync_dir):
    return [
        os.path.join(sync_dir, filename)
        for filename in sorted(os.listdir(sync_dir))
        if filename.endswith(SYNC_SUFFIX)
    ]


def sync_files_in_features(features_dir):
    paths = []
    for root, _, files in os.walk(features_dir):
        if "03_syncs/output" not in root:
            continue
        paths.extend(
            os.path.join(root, filename)
            for filename in sorted(files)
            if filename.endswith(SYNC_SUFFIX)
        )
    return paths


def collect_sync_paths(sync_dir, features_dir):
    failures = []
    paths = []
    if sync_dir and os.path.isdir(sync_dir):
        paths.extend(sync_files_in_dir(sync_dir))
    elif sync_dir:
        failures.append((sync_dir, f"sync directory not found: {sync_dir}"))

    if features_dir and os.path.isdir(features_dir):
        paths.extend(sync_files_in_features(features_dir))
    elif features_dir:
        failures.append((features_dir, f"features directory not found: {features_dir}"))

    return sorted(dict.fromkeys(paths)), failures


def matrix_table_lines(text):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## Sync Contract Matrix":
            return table_lines_after_heading(lines[index + 1:])
    return None


def table_lines_after_heading(lines):
    table_lines = []
    for line in lines:
        if line.startswith("|"):
            table_lines.append(line)
        elif table_lines and line.strip():
            break
    return table_lines


def matrix_columns(path, table_lines):
    header = split_table_row(table_lines[0])
    columns = {normalize_token(name): index for index, name in enumerate(header)}
    required = {
        "sourcerow": "Source row",
        "targetrow": "Target row",
        "whensignature": "when signature",
        "thensignature": "then signature",
    }
    failures = [
        (path, f"Sync Contract Matrix missing column: {label}")
        for key, label in required.items()
        if key not in columns
    ]
    return header, columns, failures


def parse_matrix_row(path, line, header, columns):
    cells = split_table_row(line)
    if is_separator_row(cells):
        return None, []
    if len(cells) < len(header):
        return None, [(path, f"malformed Sync Contract Matrix row: {line}")]

    when_signature = cells[columns["whensignature"]]
    then_signature = cells[columns["thensignature"]]
    when_parts = parse_when_signature(when_signature)
    then_parts = parse_then_signature(then_signature)
    failures = []
    if when_parts is None:
        failures.append((path, f"could not parse when signature: {when_signature}"))
    if then_parts is None:
        failures.append((path, f"could not parse then signature: {then_signature}"))
    if failures:
        return None, failures

    when_concept, when_action, when_outcome = when_parts
    then_concept, then_action = then_parts
    return {
        "source_row": cells[columns["sourcerow"]],
        "target_row": cells[columns["targetrow"]],
        "when_concept": when_concept,
        "when_action": when_action,
        "when_outcome": when_outcome,
        "then_concept": then_concept,
        "then_action": then_action,
    }, []


def parse_matrix(path, text):
    table_lines = matrix_table_lines(text)
    if table_lines is None:
        return [], [(path, "missing ## Sync Contract Matrix heading")]

    if len(table_lines) < 3:
        return [], [(path, "Sync Contract Matrix table has no data rows")]

    header, columns, failures = matrix_columns(path, table_lines)
    if failures:
        return [], failures

    rows = []
    for line in table_lines[1:]:
        row, row_failures = parse_matrix_row(path, line, header, columns)
        failures.extend(row_failures)
        if row:
            rows.append(row)

    return rows, failures


def collect_sync_specs(sync_paths):
    specs = []
    failures = []
    for path in sync_paths:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        stem = os.path.basename(path)[: -len(SYNC_SUFFIX)]
        decl_match = SYNC_DECL_RE.search(text)
        sync_name = decl_match.group(1) if decl_match else stem
        if not decl_match:
            failures.append((path, "missing `sync <Name>` declaration; using filename stem for parity check"))
        elif sync_name != stem:
            failures.append((path, f"filename stem '{stem}' does not match sync declaration '{sync_name}'"))

        rows, row_failures = parse_matrix(path, text)
        failures.extend(row_failures)
        for row in rows:
            specs.append({"path": path, "sync_name": sync_name, **row})
    return specs, failures


def concept_from_trigger_expression(expression):
    expr = expression.strip()
    concept_match = re.search(r"\b(\w+)Concept\.IRI\b", expr)
    if concept_match:
        return concept_match.group(1)
    if "WEB_CONCEPT_IRI" in expr or expr == "WEB_IRI":
        return "Web"
    return ""


def parse_java_sync(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    class_match = CLASS_RE.search(text)
    class_name = class_match.group(1) if class_match else os.path.splitext(os.path.basename(path))[0]

    trigger = None
    metadata_trigger = METADATA_TRIGGER_RE.search(text)
    if metadata_trigger:
        trigger = metadata_trigger.groups()
    else:
        sync_trigger = SYNC_TRIGGER_RE.search(text)
        outcome = OUTCOME_LITERAL_RE.search(text)
        if sync_trigger and outcome:
            trigger = (
                concept_from_trigger_expression(sync_trigger.group(1)),
                sync_trigger.group(2),
                outcome.group(1),
            )

    fires = None
    metadata_fires = METADATA_FIRES_RE.search(text)
    if metadata_fires:
        fires = metadata_fires.groups()

    return {
        "path": path,
        "class_name": class_name,
        "extends_sync_agent": class_match is not None,
        "singleton": "@Singleton" in text,
        "trigger": trigger,
        "fires": fires,
    }


def collect_java_syncs(sync_impl_dir):
    if not os.path.isdir(sync_impl_dir):
        return {}, [(sync_impl_dir, f"sync implementation directory not found: {sync_impl_dir}")]

    classes = {}
    for root, _, files in os.walk(sync_impl_dir):
        for filename in sorted(files):
            stem, ext = os.path.splitext(filename)
            if ext not in IMPL_EXTENSIONS:
                continue
            path = os.path.join(root, filename)
            classes[stem] = parse_java_sync(path)
    return classes, []


def trigger_matches(spec, trigger):
    if not trigger:
        return False
    concept, action, outcome = trigger
    return (
        normalize_token(concept) == normalize_token(spec["when_concept"])
        and normalize_token(action) == normalize_token(spec["when_action"])
        and normalize_token(outcome) == normalize_token(spec["when_outcome"])
    )


def fires_matches(spec, fires):
    if not fires:
        return True
    concept, action, _ = fires
    return (
        normalize_token(concept) == normalize_token(spec["then_concept"])
        and normalize_token(action) == normalize_token(spec["then_action"])
    )


def format_trigger(trigger):
    if not trigger:
        return "<not found>"
    concept, action, outcome = trigger
    return f"{concept}/{action}[{outcome}]"


def check_spec_implementation(spec, java_sync, strict_trigger):
    failures = []
    if not java_sync["extends_sync_agent"]:
        failures.append((java_sync["path"], "matching class does not extend SyncAgent"))
    if not java_sync["singleton"]:
        failures.append((java_sync["path"], "matching SyncAgent class is missing @Singleton"))
    if strict_trigger and not trigger_matches(spec, java_sync["trigger"]):
        expected = f"{spec['when_concept']}/{spec['when_action']}[{spec['when_outcome']}]"
        failures.append((
            java_sync["path"],
            f"trigger mismatch: expected {expected}, found {format_trigger(java_sync['trigger'])}",
        ))
    if strict_trigger and not fires_matches(spec, java_sync["fires"]):
        expected = f"{spec['then_concept']}/{spec['then_action']}"
        actual = "/".join(java_sync["fires"][:2]) if java_sync["fires"] else "<not declared>"
        failures.append((java_sync["path"], f"fires metadata mismatch: expected {expected}, found {actual}"))
    return failures


def check_parity(specs, java_syncs, strict_trigger):
    failures = []
    for spec in specs:
        java_sync = java_syncs.get(spec["sync_name"])
        label = f"{spec['path']} ({spec['sync_name']})"
        if not java_sync:
            failures.append((label, "no matching SyncAgent class found under --sync-impl-dir"))
            continue
        failures.extend(check_spec_implementation(spec, java_sync, strict_trigger))
    return failures


def main():
    parser = argparse.ArgumentParser(
        description="Verify every Stage 03 sync spec has a SyncAgent implementation."
    )
    parser.add_argument("--sync-dir", default="", help="Path to one 03_syncs/output directory.")
    parser.add_argument("--features-dir", default="", help="Root features/ directory; searches all 03_syncs/output dirs.")
    parser.add_argument("--sync-impl-dir", required=True, help="Directory containing Java sync implementation classes.")
    parser.add_argument(
        "--strict-trigger",
        action="store_true",
        help="Also require Java trigger/fires metadata to match Stage 03 when/then tokens exactly.",
    )
    args = parser.parse_args()

    if not args.sync_dir and not args.features_dir:
        print("ERROR: provide --sync-dir or --features-dir.", file=sys.stderr)
        sys.exit(1)

    sync_paths, path_failures = collect_sync_paths(args.sync_dir, args.features_dir)
    specs, spec_failures = collect_sync_specs(sync_paths)
    java_syncs, java_failures = collect_java_syncs(args.sync_impl_dir)
    failures = path_failures + spec_failures + java_failures + check_parity(
        specs, java_syncs, args.strict_trigger
    )

    if failures:
        print(f"FAIL: {len(failures)} sync implementation parity violation(s):\n")
        for path, message in sorted(failures):
            print(f"  {path}\n    {message}\n")
        print(
            "Every Stage 03 sync contract must lower to one @Singleton SyncAgent "
            "implementation during Stage 04e-green."
        )
        sys.exit(1)

    print(f"PASS  {len(specs)} Stage 03 sync contract(s) have matching SyncAgent implementations")
    sys.exit(0)


if __name__ == "__main__":
    main()