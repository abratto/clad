#!/usr/bin/env python3
"""Check the committed runtime descriptor against the conceptual model."""

from __future__ import annotations

import argparse
import json
import os
import sys

import check_runner as cr
import rmap


def _models(feature_root: str, features_dir: str):
    if features_dir:
        _label, sources = rmap._project_sources(features_dir)
        return [rmap.derive_model(concept, text, source=path)
                for concept, path, text in sources]
    _label, models = rmap._feature_models(feature_root)
    return models


def check_descriptor(feature_root: str, descriptor_path: str,
                     features_dir: str = "") -> list[str]:
    if not os.path.isfile(descriptor_path):
        return [f"descriptor not found: {descriptor_path}"]
    try:
        models = _models(feature_root, features_dir)
    except SystemExit as exc:
        return [str(exc)]
    expected = json.dumps(rmap.model_descriptor(models), indent=2) + "\n"
    actual = open(descriptor_path, encoding="utf-8").read()
    if actual != expected:
        scope = (f"--features-dir {features_dir}" if features_dir
                 else f"--feature {feature_root}")
        return [
            f"{descriptor_path} is stale — run "
            f"`./clad rmap {scope} --json {descriptor_path}`"
        ]
    return []


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--feature")
        group.add_argument("--features-dir")
        parser.add_argument("--descriptor", required=True)

    def body(args: argparse.Namespace) -> cr.Verdict:
        failures = check_descriptor(args.feature or "", args.descriptor,
                                    args.features_dir or "")
        if failures:
            return cr.Verdict.fail("", [cr.Problem(line) for line in failures])
        return cr.Verdict.ok("runtime schema descriptor is current")

    return cr.run_check("Check generated Rmap descriptor", body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
