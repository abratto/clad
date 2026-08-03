#!/usr/bin/env python3
"""
verify_port_spec_contract.py - Stage gate: port-spec consumers exist.

When Stage 00 produces port-spec.md, directional entries determine the
required evidence. Inbound entries require Stage 04b response-shape assertions
and Stage 04c Gherkin @contract scenarios. Outbound entries require named
adapter-boundary evidence, but do not imply an HTTP/JSON response contract.
If no port-spec.md exists, this check skips.

Usage:
  python3 verify_port_spec_contract.py \
    --port-spec <features/_system/stages/00_actor-goal/output/port-spec.md> \
    --spec-dir <04b_spec/output/> \
    --feature-dir <04c_flow-tests/output/>
"""

import argparse
import os
import re
import sys


PLACEHOLDER_RE = re.compile(r"<[^>]+>|<!--|-->")
PORT_COLUMNS = (
    "Name",
    "Direction",
    "Adapter type",
    "Owner",
    "Source contract",
    "Observable semantics",
    "Contract tests",
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def section_body(text, heading):
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def meaningful(text):
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--") or stripped.endswith("-->"):
            continue
        lines.append(stripped)
    return bool(lines) and not PLACEHOLDER_RE.search("\n".join(lines))


def table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(cells):
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def validate_port_header(lines):
    if len(lines) < 2:
        return ["port-spec.md 'Port entries' must contain a header and at least one entry"]
    if table_cells(lines[0]) != list(PORT_COLUMNS):
        return [
            "port-spec.md 'Port entries' header must be: "
            + " | ".join(PORT_COLUMNS)
        ]
    if not is_table_separator(table_cells(lines[1])):
        return ["port-spec.md 'Port entries' table is missing its separator row"]
    return []


def parse_port_entry(index, line):
    cells = table_cells(line)
    if len(cells) != len(PORT_COLUMNS):
        return None, [
            f"port-spec.md Port entries row {index} has {len(cells)} columns; "
            f"expected {len(PORT_COLUMNS)}"
        ]

    entry = dict(zip(PORT_COLUMNS, cells))
    failures = [
        f"port-spec.md Port entries row {index} is missing concrete '{column}'"
        for column, value in entry.items()
        if not meaningful(value)
    ]
    direction = entry["Direction"].strip().lower()
    valid_direction = direction in {"inbound", "outbound"}
    if not valid_direction:
        failures.append(
            f"port-spec.md Port entries row {index} has invalid Direction "
            f"'{entry['Direction']}'; expected inbound or outbound"
        )
    return entry if valid_direction else None, failures


def parse_port_entries(text):
    body = section_body(text, "Port entries")
    if not body:
        return [], [], False

    lines = [line for line in body.splitlines() if line.strip()]
    header_failures = validate_port_header(lines)
    if header_failures:
        return header_failures, [], True

    failures = []
    entries = []
    for index, line in enumerate(lines[2:], start=1):
        if line.lstrip().startswith("|"):
            entry, row_failures = parse_port_entry(index, line)
            failures.extend(row_failures)
            if entry:
                entries.append(entry)

    if not entries and not failures:
        failures.append("port-spec.md 'Port entries' has no entries")
    return failures, entries, True


def verify_port_spec(path):
    failures = []
    text = read(path)
    entry_failures, entries, directional = parse_port_entries(text)
    if directional:
        return entry_failures, entries

    # Retain the prior one-inbound-port form for existing projects.
    for heading in ("Source", "Adapter type", "Fixed conventions", "Scope"):
        body = section_body(text, heading)
        if not meaningful(body):
            failures.append(
                f"port-spec.md section '{heading}' is missing concrete content"
            )
    return failures, [{"Direction": "inbound"}]


def verify_specs(spec_dir, require_response_shapes, require_all_specs):
    failures = []
    if not os.path.isdir(spec_dir):
        return [f"SPEC directory not found: {spec_dir}"]

    spec_files = sorted(
        os.path.join(spec_dir, name)
        for name in os.listdir(spec_dir)
        if name.endswith(".spec.md")
    )
    if not spec_files:
        return [f"no .spec.md files found in {spec_dir}"]

    specs_with_shapes = []
    for path in spec_files:
        text = read(path)
        body = section_body(text, "Response shapes")
        if meaningful(body):
            specs_with_shapes.append(path)
        elif require_all_specs:
            failures.append(
                f"{path}: missing concrete '## Response shapes' section"
            )

    if require_response_shapes and not specs_with_shapes:
        failures.append(
            "no SPEC file contains a concrete '## Response shapes' section"
        )
    return failures


def verify_features(feature_dir):
    failures = []
    if not os.path.isdir(feature_dir):
        return [f"feature output directory not found: {feature_dir}"]

    feature_files = sorted(
        os.path.join(feature_dir, name)
        for name in os.listdir(feature_dir)
        if name.endswith(".feature")
    )
    if not feature_files:
        return [f"no .feature files found in {feature_dir}"]

    for path in feature_files:
        text = read(path)
        if "@contract" not in text:
            failures.append(f"{path}: missing @contract scenario")
            continue
        if not re.search(r"JSON path", text, re.IGNORECASE):
            failures.append(f"{path}: @contract scenario has no JSON path assertion")
        if not re.search(r"\btype\b", text, re.IGNORECASE):
            failures.append(f"{path}: @contract scenario has no field type assertion")
        if not re.search(r"error envelope", text, re.IGNORECASE):
            failures.append(f"{path}: @contract scenario has no error envelope assertion")
    return failures


def main():
    parser = argparse.ArgumentParser(
        description="Verify Stage 04b/04c contract artefacts when port-spec.md exists"
    )
    parser.add_argument("--port-spec", required=True)
    parser.add_argument("--spec-dir", required=True)
    parser.add_argument("--feature-dir")
    parser.add_argument(
        "--require-all-specs",
        action="store_true",
        help="Require every .spec.md file to contain concrete response shapes",
    )
    args = parser.parse_args()

    if not os.path.exists(args.port_spec):
        print(f"SKIP  no port-spec.md at {args.port_spec}")
        return 0

    failures, entries = verify_port_spec(args.port_spec)
    has_inbound_port = any(entry["Direction"].strip().lower() == "inbound" for entry in entries)
    failures.extend(verify_specs(args.spec_dir, has_inbound_port, args.require_all_specs))
    if args.feature_dir and has_inbound_port:
        failures.extend(verify_features(args.feature_dir))

    if failures:
        print(f"FAIL  port-spec contract checks failed ({len(failures)} issue(s))")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    checked = "directional port spec"
    if has_inbound_port:
        checked += " + SPEC response shapes"
        if args.feature_dir:
            checked += " + @contract scenarios"
    else:
        checked += " + outbound adapter-boundary evidence"
    print(f"PASS  port-spec contract checks passed ({checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())