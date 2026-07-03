#!/usr/bin/env python3
"""
verify_port_spec_contract.py - Stage gate: port-spec consumers exist.

When Stage 00 produces port-spec.md, Stage 04b and 04c must consume it:
SPEC output carries response-shape assertions and Gherkin carries
@contract scenarios. If no port-spec.md exists, this check skips.

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


def verify_port_spec(path):
    failures = []
    text = read(path)
    for heading in ("Source", "Adapter type", "Fixed conventions", "Scope"):
        body = section_body(text, heading)
        if not meaningful(body):
            failures.append(
                f"port-spec.md section '{heading}' is missing concrete content"
            )
    return failures


def verify_specs(spec_dir, require_all_specs):
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

    if not specs_with_shapes:
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

    failures = []
    failures.extend(verify_port_spec(args.port_spec))
    failures.extend(verify_specs(args.spec_dir, args.require_all_specs))
    if args.feature_dir:
        failures.extend(verify_features(args.feature_dir))

    if failures:
        print(f"FAIL  port-spec contract checks failed ({len(failures)} issue(s))")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    checked = "port spec + SPEC response shapes"
    if args.feature_dir:
        checked += " + @contract scenarios"
    print(f"PASS  port-spec contract checks passed ({checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())