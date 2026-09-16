#!/usr/bin/env python3
"""
verify_profile_paths.py — Profile-path integrity: configured implementation
paths must not silently audit a different tree than the feature declares.

Derived repos copied from a CLAD seed often inherit repo-root
`clad.properties` still pointing test.source.root / sync.impl.dir /
concept.impl.dir at the seed's `reference-impl/` example. Those paths
exist, so profile-aware checks do not skip — they audit the wrong tree
(silent mis-audit or false parity results).

This check cross-binds the effective configuration (repo-root
clad.properties overridden by feature-local `_config/<key>.md`, per
AGENTS.md §4a resolution order) against the feature's declared
`_config/package-and-layout.md` roots:

  BLOCKING (exit 1)
    A configured path exists on disk but resolves OUTSIDE the
    corresponding declared root:
      test.source.root                vs APP_TEST_SOURCE_ROOT
      sync.impl.dir / concept.impl.dir vs APP_SOURCE_ROOT

  WARNING (advisory, exit 0)
    A configured path resolves under the seed's `reference-impl/` tree
    while the feature declares a root elsewhere. Printed, never blocks —
    the template rule discourages but does not forbid product code in
    reference-impl/.

  Not a defect
    The feature layout itself pointing into `reference-impl/` (seed
    repositories legitimately do), or configured paths resolving inside
    the declared root.

Skips cleanly (exit 0) when the feature declares no package-and-layout
or when neither side of a pair resolves — mirroring the rest of the
quality-gate family's skip conventions.

Usage:
  python3 verify_profile_paths.py --feature features/UC-XX-<slug>

Exits 0 if all comparable pairs agree, 1 otherwise.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clad_stages as cs  # noqa: E402

PAIRS = [
    # (property key, declared layout key, human label)
    ("test.source.root", "APP_TEST_SOURCE_ROOT", "test-source root"),
    ("sync.impl.dir", "APP_SOURCE_ROOT", "sync impl dir"),
    ("concept.impl.dir", "APP_SOURCE_ROOT", "concept impl dir"),
]


def _declared_root(feature_root: str, key: str):
    """Parse APP_SOURCE_ROOT / APP_TEST_SOURCE_ROOT from the feature's
    _config/package-and-layout.md. Returns the repo-root-resolved absolute
    path, or None when absent/'TBD'/non-resolvable. Parsing is line-based
    and backtick/bold-agnostic so both the seed (`APP_SOURCE_ROOT:`) and
    template (`**APP_SOURCE_ROOT:**`) styles parse."""
    layout = os.path.join(feature_root, "_config", "package-and-layout.md")
    if not os.path.isfile(layout):
        return None
    with open(layout) as fh:
        for line in fh:
            if key not in line:
                continue
            cleaned = line.replace("`", "").replace("**", "").strip()
            # Drop the list dash, then take the text after the key up to the
            # value; the value is whatever follows 'key:' on this line.
            head, sep, tail = cleaned.partition(key)
            if not sep:
                continue
            value = tail.lstrip(" :\t*").split()[0] if tail.split() else ""
            if not value or value.upper().startswith("TBD"):
                return None
            resolved = os.path.join(cs._repo_root(feature_root), value)
            if not os.path.isdir(resolved):
                return None
            return os.path.realpath(resolved)
    return None


def _within(candidate: str, root: str) -> bool:
    """True when candidate (abs, real) is root or lies under root."""
    try:
        return os.path.commonpath([os.path.realpath(candidate),
                                   os.path.realpath(root)]) == \
            os.path.realpath(root)
    except ValueError:  # different drives on Windows — treat as outside
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Verify configured profile paths match the feature's "
                    "declared package layout")
    parser.add_argument("--feature", required=True)
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature)
    layout = os.path.join(feature_root, "_config", "package-and-layout.md")
    if not os.path.isfile(layout):
        print(f"SKIP  no package-and-layout declared for "
              f"{cs.relpath(feature_root)} — nothing to bind-check")
        sys.exit(0)

    failures = []
    warnings = []
    compared = 0

    # Fail-fast on an unfilled layout. The skeleton ships `_config/
    # package-and-layout.md` with `TBD` values; an unfilled layout resolves to
    # None and the pair is skipped quietly, so a wrong-tree mis-audit is not
    # caught. Once a feature reaches Stage 04 the layout must be concrete.
    # (Recurring friction across the conduit rebuild: `_config` shipped TBD and
    # had to be hand-filled at 04a every UC.)
    impl_output = os.path.join(feature_root, "stages", "04_implement",
                               "04a_storage-mapping", "output")
    if os.path.isdir(impl_output):
        # Strip markdown once so both the seed style (`APP_SOURCE_ROOT: TBD`)
        # and the template style (`- **APP_SOURCE_ROOT:** `TBD``) parse.
        normalized = open(layout).read().replace("`", "").replace("**", "")
        for key in ("APP_PACKAGE_ROOT", "APP_SOURCE_ROOT", "APP_TEST_SOURCE_ROOT"):
            for line in normalized.splitlines():
                if key not in line:
                    continue
                _, _, tail = line.partition(key)
                value = tail.strip().lstrip(":").strip()
                if value.upper().startswith("TBD"):
                    failures.append(
                        f"  {cs.relpath(feature_root)}: "
                        f"_config/package-and-layout.md still `TBD` for {key}; "
                        f"fill it at Stage 04a before advancing (a TBD layout "
                        f"silently skips the wrong-tree guard)")
                break

    for prop_key, layout_key, label in PAIRS:
        configured = cs._prop_path(feature_root, prop_key)
        declared = _declared_root(feature_root, layout_key)
        if not configured or not declared:
            continue  # pair not comparable — skip quietly
        compared += 1
        if _within(configured, declared):
            continue
        failures.append(
            f"  {cs.relpath(feature_root)}: {label} mismatch — "
            f"{prop_key} resolves to {cs.relpath(configured)}, outside the "
            f"declared {layout_key} {cs.relpath(declared)}")
        cfg_rooted = os.path.realpath(configured).startswith(
            os.path.realpath(os.path.join(cs._repo_root(feature_root),
                                          "reference-impl")) + os.sep)
        if cfg_rooted and not os.path.realpath(declared).startswith(
                os.path.realpath(os.path.join(cs._repo_root(feature_root),
                                              "reference-impl")) + os.sep):
            warnings.append(
                f"  NOTE {cs.relpath(feature_root)}: {prop_key} points into "
                f"the seed's reference-impl/ example while "
                f"_config/package-and-layout.md declares "
                f"{layout_key} {cs.relpath(declared)} — set "
                f"features/{os.path.basename(feature_root)}/_config/"
                f"{prop_key}.md (or re-point root clad.properties via the "
                f"maintenance route) so parity checks audit your tree")

    if failures:
        print(f"FAIL  profile-path integrity: {len(failures)} configured "
              f"path(s) resolve outside the feature's declared roots "
              f"({compared} comparable)")
        for line in failures:
            print(line)
        for line in warnings:
            print(line)
        print("Profile-aware parity checks would have audited the wrong "
              "tree. Re-point via the feature-local _config/<key>.md "
              "override or the maintenance route (R20) before advancing.")
        sys.exit(1)

    if warnings:
        for line in warnings:
            print(f"WARN {line}")
        print(f"PASS  profile-path integrity ({compared} comparable, "
              f"{len(warnings)} seed-path warning(s))")
        sys.exit(0)

    if compared == 0:
        print(f"SKIP  no configured/declared path pair resolvable for "
              f"{cs.relpath(feature_root)}")
        sys.exit(0)

    print(f"PASS  profile-path integrity ({compared} comparable — "
          f"configured paths resolve inside the declared roots)")
    sys.exit(0)


if __name__ == "__main__":
    main()
