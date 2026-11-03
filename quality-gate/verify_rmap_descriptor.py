#!/usr/bin/env python3
"""Check the committed runtime descriptor against the conceptual model."""

from __future__ import annotations

import argparse
import json
import os
import sys

import check_runner as cr
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


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--feature", required=True)
        parser.add_argument("--descriptor", required=True)

    def body(args: argparse.Namespace) -> cr.Verdict:
        failures = check_descriptor(args.feature, args.descriptor)
        if failures:
            return cr.Verdict.fail("", [cr.Problem(line) for line in failures])
        return cr.Verdict.ok("runtime schema descriptor is current")

    return cr.run_check("Check generated Rmap descriptor", body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
