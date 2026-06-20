#!/usr/bin/env python3
"""
run_feature_gate.py - Stage-aware wrapper for CLAD quality-gate scripts.

The individual verify_*.py scripts remain the source of truth for each
deterministic check. This wrapper gives agents, humans, and CI one stable
entry point for running the checks that apply to a feature stage, and can
emit either readable text or machine-readable JSON.

Usage:
  python3 quality-gate/run_feature_gate.py \
    --feature features/UC-01-register --stage 03b

  python3 quality-gate/run_feature_gate.py \
    --feature features/UC-01-register --stage all --format json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


STAGE_ALIASES = {
    "01": "01",
    "02a": "02a",
    "02b": "02b",
    "02": "02",
    "03": "03",
    "03a": "03a",
    "03b": "03b",
    "04a": "04a",
    "04b": "04b",
    "04c": "04c",
    "04d": "04d",
    "04d-red": "04d-red",
    "04d_green": "04d-green",
    "04d-green": "04d-green",
    "04e": "04e",
    "04e-red": "04e-red",
    "04e_green": "04e-green",
    "04e-green": "04e-green",
    "05": "05",
    "all": "all",
}

VERIFY_FILE_MANIFEST = "verify_file_manifest.py"
VERIFY_SCENARIO_COVERAGE = "verify_scenario_coverage.py"
SCENARIO_COVERAGE = "scenario coverage"
MISSING_GOALS = Path("missing-goals.md")


def slugify(name: str) -> str:
    value = name.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def parse_scenarios(usecase: Path) -> list[str]:
    names = []
    for line in read_text(usecase).splitlines():
        match = re.match(r"^### Scenario:\s+(.+)$", line.strip())
        if match:
            names.append(match.group(1).strip())
    return names


def parse_concepts_from_resp_map(resp_map: Path) -> list[str]:
    concepts = []
    in_table = False
    for line in read_text(resp_map).splitlines():
        if line.strip().startswith("| Concept | Owned state"):
            in_table = True
            continue
        if not in_table:
            continue
        if re.match(r"^\|[\s\-:]+\|", line):
            continue
        if not line.startswith("|"):
            break
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 3:
            concept = parts[1].strip("`")
            if concept and concept.lower() != "web":
                concepts.append(concept)
    return concepts


def concept_files(concept_dir: Path, suffix: str) -> list[str]:
    if not concept_dir.is_dir():
        return []
    return sorted(path.name.removesuffix(suffix) for path in concept_dir.glob(f"*{suffix}"))


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def read_layout_value(layout: Path, key: str) -> str | None:
    pattern = re.compile(rf"^- \*\*{re.escape(key)}:\*\*\s+`([^`]+)`")
    for line in read_text(layout).splitlines():
        match = pattern.match(line.strip())
        if match:
            value = match.group(1).strip()
            if value and value != "TBD":
                return value
    return None


class Check:
    def __init__(self, name: str, command: list[str], required: list[Path] | None = None):
        self.name = name
        self.command = command
        self.required = required or []


def command(script_dir: Path, script: str, *args: str | Path) -> list[str]:
    return [sys.executable, str(script_dir / script), *[str(arg) for arg in args]]


def build_checks(repo: Path, feature: Path, stage: str) -> list[Check]:
    script_dir = repo / "quality-gate"
    stages = feature / "stages"
    config = feature / "_config"
    goals = first_existing([
        feature / "stages" / "00_actor-goal" / "output" / "goals.md",
        repo / "features" / "_system" / "stages" / "00_actor-goal" / "output" / "goals.md",
    ])
    goals_path = goals or MISSING_GOALS
    usecase = stages / "01_usecase" / "output" / "usecase.md"
    resp_map = stages / "02a_responsibility-map" / "output" / "responsibility-map.md"
    chain_dir = stages / "02b_chain-table" / "output"
    concept_dir = stages / "02_concepts" / "output"
    sync_dir = stages / "03_syncs" / "output"
    dep_dir = stages / "03a_dependency-review" / "output"
    data_dir = stages / "03b_data-model" / "output"
    impl = stages / "04_implement"
    storage_dir = impl / "04a_storage-mapping" / "output"
    spec_dir = impl / "04b_spec" / "output"
    flow_dir = impl / "04c_flow-tests" / "output"
    concept_derivation = impl / "04d_concept-tdd" / "04d_red-tests" / "output" / "concept-test-derivation.md"
    sync_derivation = impl / "04e_sync-tdd" / "04e_red-tests" / "output" / "sync-test-derivation.md"
    configured_test_root = read_layout_value(config / "package-and-layout.md", "APP_TEST_SOURCE_ROOT")
    test_source_root = repo / configured_test_root if configured_test_root else repo / "app" / "backend" / "src" / "test" / "java"
    feature_files_dir = repo / "app" / "backend" / "src" / "test" / "resources" / "features"

    scenarios = parse_scenarios(usecase)
    concepts = parse_concepts_from_resp_map(resp_map)
    if not concepts:
        concepts = concept_files(concept_dir, ".concept.md")
    storage_expected = "_NOT_APPLICABLE.md" if (storage_dir / "_NOT_APPLICABLE.md").is_file() else ",".join(f"{name}.storage.md" for name in concepts)

    checks_by_stage: dict[str, list[Check]] = {
        "01": [
            Check("01 manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", stages / "01_usecase" / "output", "--expected", "usecase.md"), [usecase]),
            Check(SCENARIO_COVERAGE, command(script_dir, VERIFY_SCENARIO_COVERAGE, "--goals", goals_path, "--usecase", usecase, "--chain-dir", chain_dir, "--sync-dir", sync_dir), [goals_path, usecase]),
        ],
        "02a": [
            Check("02a manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", stages / "02a_responsibility-map" / "output", "--expected", "responsibility-map.md"), [resp_map]),
        ],
        "02b": [
            Check("02b manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", chain_dir, "--expected", ",".join(f"{slugify(name)}-chain.md" for name in scenarios)), [usecase, chain_dir]),
            Check(SCENARIO_COVERAGE, command(script_dir, VERIFY_SCENARIO_COVERAGE, "--goals", goals_path, "--usecase", usecase, "--chain-dir", chain_dir, "--sync-dir", sync_dir), [goals_path, usecase, chain_dir]),
        ],
        "02": [
            Check("02 manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", concept_dir, "--expected", ",".join(f"{name}.concept.md" for name in concepts)), [resp_map, concept_dir]),
        ],
        "03": [
            Check("sync matrix", command(script_dir, "verify_sync_matrix.py", "--sync-dir", sync_dir, "--chain-dir", chain_dir), [sync_dir]),
            Check(SCENARIO_COVERAGE, command(script_dir, VERIFY_SCENARIO_COVERAGE, "--goals", goals_path, "--usecase", usecase, "--chain-dir", chain_dir, "--sync-dir", sync_dir), [goals_path, usecase, chain_dir, sync_dir]),
        ],
        "03a": [
            Check("03a manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", dep_dir, "--expected", ",".join([*(f"{name}-card.md" for name in concepts), "pattern-d-summary.md"])), [concept_dir, dep_dir]),
        ],
        "03b": [
            Check("03b manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", data_dir, "--expected", ",".join(f"{name}.data-model.md" for name in concepts)), [concept_dir, data_dir]),
            Check("data model", command(script_dir, "verify_data_model.py", "--data-dir", data_dir, "--concept-dir", concept_dir), [data_dir, concept_dir]),
        ],
        "04a": [
            Check("04a manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", storage_dir, "--expected", storage_expected), [concept_dir, storage_dir]),
        ],
        "04b": [
            Check("04b manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", spec_dir, "--expected", ",".join(f"{name}.spec.md" for name in concepts)), [concept_dir, spec_dir]),
            Check("spec parity", command(script_dir, "verify_spec_parity.py", "--concept-dir", concept_dir, "--spec-dir", spec_dir), [concept_dir, spec_dir]),
        ],
        "04c": [
            Check("test framework config", command(script_dir, "verify_test_framework_config.py", "--config-dir", config, "--clad-properties", repo / "clad.properties", "--feature-output-dir", flow_dir, "--feature-files-dir", feature_files_dir), [config, flow_dir]),
        ],
        "04d-red": [
            Check("04d-red manifest", command(script_dir, VERIFY_FILE_MANIFEST, "--dir", concept_derivation.parent, "--expected", "concept-test-derivation.md"), [concept_derivation]),
            Check("concept test derivation", command(script_dir, "verify_concept_test_derivation.py", "--spec-dir", spec_dir, "--derivation", concept_derivation, "--test-source-root", test_source_root), [spec_dir, concept_derivation, test_source_root]),
        ],
        "04d": [],
        "04d-green": [],
        "04e-red": [
            Check("04e-red manifest", command(script_dir, "verify_file_manifest.py", "--dir", sync_derivation.parent, "--expected", "sync-test-derivation.md"), [sync_derivation]),
        ],
        "04e": [],
        "04e-green": [],
        "05": [],
    }

    if stage == "all":
        ordered = ["01", "02a", "02b", "02", "03", "03a", "03b", "04a", "04b", "04c", "04d-red", "04e-red"]
        return [check for key in ordered for check in checks_by_stage[key]]
    return checks_by_stage[stage]


def feature_label(repo: Path, feature: Path) -> str:
    try:
        return str(feature.relative_to(repo))
    except ValueError:
        return str(feature)


def run_check(check: Check) -> dict[str, object]:
    missing = [str(path) for path in check.required if path is None or not path.exists()]
    if missing:
        return {
            "name": check.name,
            "status": "fail",
            "exitCode": None,
            "command": check.command,
            "stdout": "",
            "stderr": "",
            "missing": missing,
        }
    completed = subprocess.run(check.command, text=True, capture_output=True, check=False)
    return {
        "name": check.name,
        "status": "pass" if completed.returncode == 0 else "fail",
        "exitCode": completed.returncode,
        "command": check.command,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "missing": [],
    }


def print_text_report(report: dict[str, object]) -> None:
    for result in report["checks"]:
        prefix = "PASS" if result["status"] == "pass" else "FAIL"
        print(f"{prefix}  {result['name']}")
        for missing in result["missing"]:
            print(f"      missing: {missing}")
        if result["stdout"]:
            for line in str(result["stdout"]).splitlines():
                print(f"      {line}")
        if result["stderr"]:
            for line in str(result["stderr"]).splitlines():
                print(f"      STDERR {line}")
    print(f"{str(report['status']).upper()}  {len(report['checks'])} check(s) for {report['feature']} stage {report['stage']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CLAD quality-gate checks for a feature stage")
    parser.add_argument("--feature", required=True, help="Path to features/UC-XX-<slug>")
    parser.add_argument("--stage", required=True, choices=sorted(STAGE_ALIASES), help="Stage to check, or all")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    repo = Path.cwd()
    feature = Path(args.feature)
    if not feature.is_absolute():
        feature = repo / feature
    stage = STAGE_ALIASES[args.stage]

    if not feature.is_dir():
        print(f"FAIL  feature directory not found: {feature}", file=sys.stderr)
        return 1

    checks = build_checks(repo, feature, stage)
    results = [run_check(check) for check in checks]
    passed = bool(results) and all(result["status"] == "pass" for result in results)
    report = {
        "feature": feature_label(repo, feature),
        "stage": stage,
        "status": "pass" if passed else "fail",
        "checks": results,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print_text_report(report)

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())