#!/usr/bin/env python3
"""
create_feature.py — bootstrap a new feature from the skeleton (D7).

Copies `templates/feature-skeleton` to `features/<slug>` and fills
`_config/package-and-layout.md` from `clad.properties`, so the shipped `TBD`
layout — which blocks Stage 04a — is replaced up front instead of by hand.

Usage:
  python3 create_feature.py --slug UC-08-<slug> [--repo-root .]
"""

import argparse
import os
import re
import shutil
import sys


def read_properties(repo_root: str) -> dict:
    props = {}
    path = os.path.join(repo_root, "clad.properties")
    if not os.path.isfile(path):
        return props
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            props[key.strip()] = value.strip()
    return props


def layout_values(props: dict) -> dict:
    """Derive the `_config/package-and-layout.md` values from clad.properties.

    The package root and source roots are read off `concept.impl.dir` (the
    package-annotated impl path) and `test.source.root`; nothing is invented."""
    impl = props.get("concept.impl.dir", "") or props.get("sync.impl.dir", "")
    package_root, source_root, profile = "TBD", "TBD", "TBD"
    marker = "/src/main/java/"
    if marker in impl:
        source_root = impl.split(marker, 1)[0] + "/src/main/java"
        package_root = impl.split(marker, 1)[1].strip("/").replace("/", ".")
    if impl.startswith("reference-impl/"):
        profile = impl.split("/", 2)[1]
        profile = f"reference-impl/{profile}"
    return {
        "APP_PACKAGE_ROOT": package_root,
        "APP_SOURCE_ROOT": source_root,
        "APP_TEST_SOURCE_ROOT": props.get("test.source.root", "TBD") or "TBD",
        "REFERENCE_PROFILE": profile,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap a new feature from the skeleton")
    parser.add_argument("--slug", required=True, help="e.g. UC-08-<slug>")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--skeleton", default="",
                        help="Skeleton root (default: templates/feature-skeleton)")
    args = parser.parse_args()

    repo = os.path.abspath(args.repo_root)
    skeleton = os.path.abspath(args.skeleton) if args.skeleton else os.path.join(
        repo, "templates", "feature-skeleton")
    dest = os.path.join(repo, "features", args.slug)

    if not os.path.isdir(skeleton):
        print(f"FAIL  skeleton not found: {skeleton}")
        return 1
    if os.path.exists(dest):
        print(f"FAIL  {dest} already exists")
        return 1

    shutil.copytree(skeleton, dest)
    values = layout_values(read_properties(repo))

    layout = os.path.join(dest, "_config", "package-and-layout.md")
    if os.path.isfile(layout):
        with open(layout, encoding="utf-8") as handle:
            text = handle.read()
        for key, value in values.items():
            text = re.sub(rf"(\*\*{re.escape(key)}:\*\*\s*)`[^`]*`",
                          rf"\g<1>`{value}`", text)
        with open(layout, "w", encoding="utf-8") as handle:
            handle.write(text)

    print(f"WROTE  {dest}")
    for key, value in values.items():
        print(f"  {key}: {value}")
    print("  Next: fill README.md and _config/voice.md, then start Stage 01.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
