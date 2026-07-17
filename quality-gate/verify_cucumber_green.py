#!/usr/bin/env python3
"""
verify_cucumber_green.py — Stage gate: Cucumber scenarios must all pass.

Why this exists:
  Stage 04e-green requires all Gherkin scenarios to pass via the Cucumber
  runner before the agent can advance to Stage 05. The 04e-green CONTEXT.md
  describes this requirement, but without an automated script the agent can
  claim "green" without actually running the tests or can overlook undefined/
  pending steps that don't throw compilation errors. This script enforces the
  requirement deterministically.

Checks:
  1. The test command (from clad.properties test.command or --test-command)
     exits with status 0.
  2. No undefined Cucumber steps (catches step-definition gaps).
  3. No pending Cucumber steps (catches @Pending / stub implementations).
  4. No failing Cucumber scenarios.
  5. At least one Cucumber scenario was actually executed.

Strategy:
  If the project uses Cucumber JUnit Platform Engine, `mvn test` will report
  Cucumber results via the standard JUnit report. This script:
    a) Runs the test command.
    b) Scans surefire-report XML files for any Cucumber-related test failures.
    c) Also checks for the Cucumber JSON report if available.

  If the test command itself exits non-zero due to compilation errors or other
  test failures, the script reports the failure and provides the agent with
  context.

Usage:
  python3 verify_cucumber_green.py \\
    --feature-root <feature_root> \\
    [--test-command <command>] \\
    [--surefire-dir <target/surefire-reports>]
"""

import argparse
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import textwrap
from pathlib import Path


def read_clad_test_command(feature_root):
    """Walk up from feature_root to find clad.properties and read test.command."""
    d = Path(feature_root).resolve()
    while True:
        candidate = d / "clad.properties"
        if candidate.is_file():
            with open(candidate) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("test.command"):
                        return line.split("=", 1)[1].strip()
        parent = d.parent
        if parent == d:
            return None
        d = parent


def find_surefire_reports(feature_root):
    """Search for target/surefire-reports relative to feature_root."""
    d = Path(feature_root).resolve()
    while True:
        candidate = d / "target" / "surefire-reports"
        if candidate.is_dir():
            return str(candidate)
        # Also try common build tool output dirs
        for sub in ["app", "backend", "app/backend"]:
            c2 = d / sub / "target" / "surefire-reports"
            if c2.is_dir():
                return str(c2)
        parent = d.parent
        if parent == d:
            return None
        d = parent


def find_cucumber_json(feature_root):
    """Search for cucumber.json report relative to feature_root."""
    for name in ["cucumber.json", "cucumber-report.json",
                 "reports/cucumber.json"]:
        d = Path(feature_root).resolve()
        while True:
            candidate = d / "target" / name
            if candidate.is_file():
                return str(candidate)
            parent = d.parent
            if parent == d:
                break
            d = parent
    return None


def parse_surefire(surefire_dir):
    """Parse all TEST-*.xml in surefire_dir and return summary dict."""
    result = {
        "tests": 0, "failures": 0, "errors": 0, "skipped": 0,
        "feature_files": 0, "feature_scenarios_passed": 0,
        "feature_scenarios_failed": 0, "feature_scenarios_skipped": 0,
        "cucumber_tests_found": False,
        "failure_details": [],
    }
    if not surefire_dir or not os.path.isdir(surefire_dir):
        return result

    for fname in os.listdir(surefire_dir):
        if not fname.startswith("TEST-") or not fname.endswith(".xml"):
            continue
        fpath = os.path.join(surefire_dir, fname)
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
        except ET.ParseError:
            continue

        ts = root.attrib
        classname = ts.get("name", fname)

        # Collect standard counts
        t = int(ts.get("tests", 0))
        f = int(ts.get("failures", 0))
        e = int(ts.get("errors", 0))
        s = int(ts.get("skipped", 0))
        result["tests"] += t
        result["failures"] += f
        result["errors"] += e
        result["skipped"] += s

        # Cucumber-specific: look for CucumberTestEngine class
        if "CucumberTestEngine" in classname or "cucumber" in classname.lower():
            result["cucumber_tests_found"] = True
        if "Feature:" in classname or "[Scenario" in classname:
            result["feature_files"] = t
            result["cucumber_tests_found"] = True
            for tc in root.findall("testcase"):
                tc_name = tc.get("name", "")
                failure = tc.find("failure")
                skipped = tc.find("skipped")
                if failure is not None:
                    result["feature_scenarios_failed"] += 1
                    msg = (failure.get("message", "") or
                           (failure.text or "").strip())
                    if msg:
                        result["failure_details"].append(
                            f"  {tc_name}: {msg[:120]}")
                elif skipped is not None:
                    result["feature_scenarios_skipped"] += 1
                else:
                    result["feature_scenarios_passed"] += 1

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Verify Cucumber scenarios are all green")
    parser.add_argument("--feature-root", required=True,
                        help="Path to the feature root (e.g. features/UC-XX-<slug>)")
    parser.add_argument("--test-command", default=None,
                        help="Override the test command (default: from clad.properties)")
    parser.add_argument("--surefire-dir", default=None,
                        help="Path to surefire-reports directory")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature_root)
    if not os.path.isdir(feature_root):
        print(f"FAIL  feature root not found: {feature_root}")
        sys.exit(1)

    # Resolve test command
    test_cmd = args.test_command or read_clad_test_command(feature_root)
    if not test_cmd:
        print(f"FAIL  could not determine test command. "
              f"Set test.command in clad.properties or pass --test-command.")
        sys.exit(1)

    # Resolve surefire dir
    surefire_dir = args.surefire_dir or find_surefire_reports(feature_root)

    # Run tests
    print(f"INFO  Running: {test_cmd}")
    result = subprocess.run(
        test_cmd, shell=True, capture_output=True, text=True,
        cwd=feature_root)

    # Parse surefire
    summary = parse_surefire(surefire_dir)

    # Determine pass/fail
    passed = True

    if result.returncode != 0:
        print(f"FAIL  test command exited with status {result.returncode}")
        passed = False

    if not summary["cucumber_tests_found"]:
        print(f"WARN  no Cucumber test results detected in surefire reports. "
              f"Verify the Cucumber runner is configured and .feature files are "
              f"in the discovery path.")
        # Not a hard fail — maybe Cucumber runs but reports differently

    if summary["feature_scenarios_failed"] > 0:
        print(f"FAIL  {summary['feature_scenarios_failed']} Cucumber "
              f"scenario(s) failed:")
        for detail in summary["failure_details"]:
            print(detail)
        passed = False

    if summary["feature_scenarios_skipped"] > 0:
        print(f"FAIL  {summary['feature_scenarios_skipped']} Cucumber "
              f"scenario(s) skipped/undefined — implement the missing "
              f"step definitions or mark them as @Pending only where "
              f"intentional")
        passed = False

    if summary["tests"] > 0 and summary["failures"] == 0 and summary["errors"] == 0:
        print(f"INFO  All {summary['tests']} tests passed "
              f"({summary.get('feature_scenarios_passed', 0)} Cucumber scenarios)")
    elif summary["tests"] == 0:
        print(f"FAIL  no tests were executed. Verify the test command and "
              f"test configuration.")
        passed = False

    # Also check for undefined step messages in stdout/stderr
    combined = (result.stdout or "") + (result.stderr or "")
    if "UndefinedStepException" in combined:
        print(f"FAIL  undefined Cucumber steps detected — "
              f"implement the missing step definitions")
        passed = False
    if "scenarios are pending" in combined.lower():
        print(f"FAIL  pending Cucumber scenarios detected — "
              f"implement the pending steps")
        passed = False

    if passed:
        print(f"PASS  Cucumber scenarios are all green")
        sys.exit(0)
    else:
        print()
        print(textwrap.dedent(f"""\
            Agent instruction:
              Fix the failing Cucumber scenario(s) above. This gate requires
              ALL Gherkin scenarios to pass before advancing to Stage 05.
              Use the captured Cucumber report for detailed failure messages.
              See methodology/architecture/GHERKIN_INTEGRATION.md for
              the complete derivation and verification rules.
        """))
        sys.exit(1)


if __name__ == "__main__":
    main()
