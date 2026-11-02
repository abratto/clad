#!/usr/bin/env python3
"""Check the committed runtime descriptor against the conceptual model."""

from __future__ import annotations

import argparse
import json
import os
import sys

import rmap


def check_descriptor(feature_root: str, descriptor_path: str) -> list[str]:
    if not os.path.isfile(descriptor_path):
        return [f"descriptor not found: {descriptor_path}"]
    try:
        _label, models = rmap._feature_models(feature_root)
    except SystemExit as exc:
        return [str(exc)]
    expected = json.dumps(rmap.model_descriptor(models), indent=2) + "\n"
    actual = open(descriptor_path, encoding="utf-8").read()
    if actual != expected:
        return [
            f"{descriptor_path} is stale — run "
            f"`./clad rmap --feature {feature_root} --json {descriptor_path}`"
        ]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated Rmap descriptor")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--descriptor", required=True)
    args = parser.parse_args()
    failures = check_descriptor(args.feature, args.descriptor)
    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        return 1
    print("PASS  runtime schema descriptor is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
