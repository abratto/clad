#!/usr/bin/env python3
"""Fast conceptual-model drift check (no Java build required).

For every feature, the committed `03b_data-model/output/*.data-model.md` must
still agree with the concept's approved `## State`. This is the local, fast
half of the Rmap drift guard; the Flyway/jOOQ byte comparison remains in the
profile tests.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import clad_stages as cs
import rmap
import verify_rmap_descriptor as descriptor

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent


def features(include_examples: bool, features_dir: str = ""):
    root = Path(features_dir) if features_dir else REPO_ROOT / "features"
    if root.is_dir():
        for path in sorted(root.glob("UC-*")):
            if path.is_dir():
                yield path
    if include_examples and not features_dir:
        examples = REPO_ROOT / "examples"
        if examples.is_dir():
            for path in sorted(examples.glob("UC-*")):
                if path.is_dir():
                    yield path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Stage 03b models against concept state")
    parser.add_argument("--include-examples", action="store_true")
    parser.add_argument("--features-dir", default="",
                        help="Feature root to scan (default <repo>/features)")
    args = parser.parse_args()

    failed = False
    checked = 0
    for feature in features(args.include_examples, args.features_dir):
        data_dir = Path(cs.DATA_DIR(str(feature)))
        if not data_dir.is_dir():
            continue
        # A freshly bootstrapped feature has the skeleton's empty
        # `03b_data-model/output/` (only `.gitkeep`). That is not a data-model
        # set; the stage manifest owns completeness. Only drift-check features
        # that actually have models. (Experiment: every new UC failed the
        # project-level model check before Stage 03b.)
        if not any(data_dir.glob("*.data-model.md")):
            continue
        concept_dirs = [d for d in cs.concept_source_dirs(str(feature))
                        if os.path.isdir(d)]
        if not concept_dirs:
            continue
        checked += 1
        proc = subprocess.run(
            [sys.executable, str(HERE / "verify_data_model.py"),
             "--data-dir", str(data_dir),
             *[arg for directory in concept_dirs
               for arg in ("--concept-dir", directory)]],
            cwd=str(REPO_ROOT), capture_output=True, text=True)
        detail = ((proc.stdout or "") + (proc.stderr or "")).strip()
        if proc.returncode != 0:
            failed = True
            print(f"FAIL  {feature.name}")
            for line in detail.splitlines()[:12]:
                print(f"      {line}")
        else:
            schema = feature / "_generated" / "rmap-schema.json"
            if schema.is_file():
                failures = descriptor.check_descriptor(str(feature), str(schema))
                if failures:
                    failed = True
                    print(f"FAIL  {feature.name} (schema descriptor)")
                    for line in failures:
                        print(f"      {line}")
                    continue
            print(f"PASS  {feature.name}")

    if not checked:
        print("SKIP  no Stage 03b data models to check")
        return 0
    print(f"{'FAIL' if failed else 'PASS'}  {checked} feature model set(s) checked")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
