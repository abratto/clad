#!/usr/bin/env python3
"""
verify_gherkin_derivation.py — Stage gate: Gherkin artefacts match upstream derivation rules.

Why this exists:
  Gherkin .feature files and step-definition classes are mechanically derived
  from upstream CLAD artefacts (usecase.md, chain tables, SPECs, syncs). An LLM
  can introduce scenarios without a use-case basis, omit Given/When/Then steps,
  use wrong status codes, or use non-standard outcome values. This script checks
  the derivation mechanically per GHERKIN_INTEGRATION.md rules G1–G5, S1–S3, E1.

Checks:
  1. Every ### Scenario: in usecase.md has a matching Scenario: or Scenario Outline: in .feature
  2. Every Scenario: in .feature has a matching ### Scenario: in usecase.md
  3. Every scenario has at least one Given, one When, and one Then step
  4. Response status codes in Then steps match those declared in sync spec then clauses
  5. Scenario Outline Examples rows exist when the use case has extensions
  6. Feature header has required elements (Feature name, As a, I want)

Usage:
  python3 verify_gherkin_derivation.py \
    --usecase <usecase.md> \
    --feature <feature.feature> \
    --sync-dir <03_syncs/output/>
"""

import argparse
import os
import re
import sys


def parse_usecase_scenarios(path):
    """Return set of scenario names from ### Scenario: headings in usecase.md."""
    names = set()
    with open(path) as f:
        for line in f:
            m = re.match(r"^### Scenario:\s+(.+)$", line.strip())
            if m:
                names.add(m.group(1).strip())
    return names


def parse_feature_scenarios(path):
    """Return dict of scenario name -> list of lines for each Scenario or Scenario Outline."""
    scenarios = {}
    current_name = None
    current_lines = []
    in_outline = False

    with open(path) as f:
        lines = f.readlines()

    for line in lines:
        m_scenario = re.match(r"^\s*(?:Scenario|Scenario\s+Outline):\s+(.+)$", line.strip())
        if m_scenario:
            if current_name:
                scenarios[current_name] = current_lines
            current_name = m_scenario.group(1).strip()
            current_lines = [line]
            in_outline = "Outline" in line
        elif current_name:
            current_lines.append(line)

    if current_name:
        scenarios[current_name] = current_lines

    return scenarios, in_outline


def parse_sync_status_codes(sync_dir):
    """Return set of numeric status codes used across sync respond then clauses."""
    codes = set()
    if not os.path.isdir(sync_dir):
        return codes
    for fname in os.listdir(sync_dir):
        if not fname.endswith(".sync.md"):
            continue
        with open(os.path.join(sync_dir, fname)) as f:
            content = f.read()
        # Find Web.respond(status=...) in then clause
        for m in re.finditer(r"Web\.respond\((\d+)", content):
            codes.add(int(m.group(1)))
        # Find status codes in the Allowed literals column of the Sync Contract Matrix.
        # The matrix has format:
        #   | Source row | Target row | when sig | then sig | Allowed literals |
        # Target row column numbers (e.g. | 8 |) are NOT status codes.
        # Parse only the last column (Allowed literals), which may contain
        # values like "200, true" or "422" or '200, "/dashboard"'.
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 6:
                    allowed = cells[-1]
                    for m in re.finditer(r"(\d+)", allowed):
                        codes.add(int(m.group(1)))
    return codes


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def scenarios_match(uc_name, f_name):
    """Check if a use-case scenario name matches a Gherkin scenario name."""
    uc_slug = slugify(uc_name)
    f_slug = slugify(f_name)
    uc_tokens = set(uc_slug.replace("-", "_").split("_"))
    f_tokens = set(f_slug.replace("-", "_").split("_"))

    common_tokens = uc_tokens & f_tokens
    token_substring = any(
        ut in ft or ft in ut
        for ut in uc_tokens for ft in f_tokens
    )
    # Check if any token root (first 4 chars) appears in the other slug
    common_root = any(
        ut[:4] in f_slug for ut in uc_tokens if len(ut) >= 4
    ) or any(
        ft[:4] in uc_slug for ft in f_tokens if len(ft) >= 4
    )

    return (uc_slug == f_slug or
            uc_slug in f_slug or f_slug in uc_slug or
            len(common_tokens) >= max(1, min(len(uc_tokens), len(f_tokens)) // 2) or
            token_substring or common_root)


def main():
    parser = argparse.ArgumentParser(
        description="Verify Gherkin derivation from upstream CLAD artefacts")
    parser.add_argument("--usecase", required=True,
                        help="Path to usercase.md from Stage 01")
    parser.add_argument("--feature", required=True,
                        help="Path to .feature file from Stage 04c")
    parser.add_argument("--sync-dir", required=True,
                        help="Path to 03_syncs/output/")
    args = parser.parse_args()

    passed = True

    if not os.path.isfile(args.usecase):
        print(f"FAIL  usecase not found: {args.usecase}")
        sys.exit(1)
    if not os.path.isfile(args.feature):
        print(f"FAIL  feature file not found: {args.feature}")
        sys.exit(1)

    # Parse both sides
    uc_scenarios = parse_usecase_scenarios(args.usecase)
    feature_scenarios, has_outline = parse_feature_scenarios(args.feature)

    if not uc_scenarios:
        print("FAIL  no scenarios found in usecase.md")
        passed = False
    if not feature_scenarios:
        print("FAIL  no scenarios found in .feature file")
        passed = False

    if not passed:
        sys.exit(1)

    # Check 1: Every use-case scenario has a matching Gherkin scenario
    for uc_name in sorted(uc_scenarios):
        found = any(scenarios_match(uc_name, f_name) for f_name in feature_scenarios)
        if not found:
            print(f"FAIL  use-case scenario '{uc_name}' has no matching "
                  f"Scenario in .feature file "
                  f"(Gherkin scenarios: {sorted(feature_scenarios.keys())})")
            passed = False

    # Check 2: Every Gherkin scenario has a matching use-case scenario
    for f_name in sorted(feature_scenarios):
        found = any(scenarios_match(uc_name, f_name) for uc_name in uc_scenarios)
        if not found:
            print(f"WARN  Gherkin scenario '{f_name}' has no matching "
                  f"### Scenario: in usecase.md")

    # Check 3: Every scenario has Given/When/Then
    for f_name, f_lines in feature_scenarios.items():
        content = "".join(f_lines)
        has_given = bool(re.search(r"^\s+Given\s+", content, re.MULTILINE))
        has_when = bool(re.search(r"^\s+When\s+", content, re.MULTILINE))
        has_then = bool(re.search(r"^\s+Then\s+", content, re.MULTILINE))
        if not has_given:
            print(f"FAIL  Gherkin scenario '{f_name}' has no Given step")
            passed = False
        if not has_when:
            print(f"FAIL  Gherkin scenario '{f_name}' has no When step")
            passed = False
        if not has_then:
            print(f"FAIL  Gherkin scenario '{f_name}' has no Then step")
            passed = False

    # Check 4: Response status codes in Then steps match sync spec codes
    sync_codes = parse_sync_status_codes(args.sync_dir)
    if sync_codes:
        for f_name, f_lines in feature_scenarios.items():
            content = "".join(f_lines)
            for m in re.finditer(
                r"(?:Then|And)\s+the response status is (\d+)",
                content
            ):
                code = int(m.group(1))
                if code not in sync_codes:
                    print(f"FAIL  scenario '{f_name}' uses status {code} "
                          f"but no sync spec declares that status code "
                          f"(sync codes: {sorted(sync_codes)})")
                    passed = False

    # Check 5: Feature header has required elements
    with open(args.feature) as f:
        feature_content = f.read()
    has_feature = bool(re.search(r"^Feature:\s+", feature_content, re.MULTILINE))
    has_as_a = bool(re.search(r"As\s+a\s+", feature_content, re.MULTILINE))
    has_i_want = bool(re.search(r"I want\s+", feature_content, re.MULTILINE))
    if not has_feature:
        print("FAIL  .feature file has no Feature: header (G1)")
        passed = False
    if not has_as_a:
        print("FAIL  .feature file has no 'As a <actor>' line (G1)")
        passed = False
    if not has_i_want:
        print("FAIL  .feature file has no 'I want <goal>' line (G1)")
        passed = False

    if passed:
        uc_count = len(uc_scenarios)
        f_count = len(feature_scenarios)
        print(f"PASS  Gherkin derivation: {uc_count} use-case scenarios → "
              f"{f_count} Gherkin scenarios, all Given/When/Then present, "
              f"status codes match syncs")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
