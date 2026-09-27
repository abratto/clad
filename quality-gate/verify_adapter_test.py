#!/usr/bin/env python3
"""verify_adapter_test.py — when a feature exposes an adapter surface, a
profile-specific end-to-end adapter test must exist (blocking).

Why this exists:
  Stage 04c step 6 requires a profile-specific integration test that exercises
  the adapter surface end-to-end — an HTTP request hitting the controller, the
  bootstrap (`Web`) concept, the business concepts/syncs, and back to the HTTP
  response — distinct from the Gherkin flow tests (which assert the action token
  chain). Until now that requirement was only an advisory Stage-05 warning
  (`verify_close_evidence.py`), so a worker could skip it and still pass.

  This check blocks at the stage that authors it:
    * Stage 04c — a matching test file must EXIST. At 04c the outer loop is red,
      so a `@Disabled` test is acceptable; presence is what is enforced.
    * Stage 05 — `--require-enabled`: the test must exist AND be enabled (the
      feature is closed and green).

  It is profile-aware: a feature with no adapter surface (no `port-spec.md`
  inbound entry, no `Web` bootstrap in its chain/use-case) or with no configured
  `test.source.root` reports SKIP, not failure — so non-adapter features and
  profiles are unaffected.

Usage:
  python3 verify_adapter_test.py --feature-root <UC> --test-source-root <dir> [--require-enabled]
Exit: 0 pass/skip, 1 a declared adapter surface has no (enabled) adapter test.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clad_stages as cs  # noqa: E402

ADAPTER_TEST_RE = re.compile(r"(?:Flow|Integration|Contract|IT)Test?$|IT$")
WEB_CHAIN_RE = re.compile(r"Web[/.](?:request|handle|respond)")


def _port_spec_inbound(feature_root: str) -> bool:
    path = cs._port_spec(feature_root)
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return bool(re.search(r"\binbound\b", fh.read(), re.IGNORECASE))
    except OSError:
        return False


def _web_in_chain(feature_root: str) -> bool:
    chain_dir = cs.CHAIN_DIR(feature_root)
    if not os.path.isdir(chain_dir):
        return False
    for name in sorted(os.listdir(chain_dir)):
        if not name.endswith("-chain.md") or name.endswith("-all-scenarios-chain.md"):
            continue
        try:
            with open(os.path.join(chain_dir, name), encoding="utf-8",
                      errors="replace") as fh:
                if WEB_CHAIN_RE.search(fh.read()):
                    return True
        except OSError:
            continue
    return False


def has_adapter_surface(feature_root: str) -> bool:
    if _port_spec_inbound(feature_root):
        return True
    if _web_in_chain(feature_root):
        return True
    usecase = cs._usecase(feature_root)
    if os.path.isfile(usecase):
        try:
            with open(usecase, encoding="utf-8", errors="replace") as fh:
                return bool(re.search(r"\bWeb\b", fh.read()))
        except OSError:
            return False
    return False


def find_adapter_tests(test_root: str):
    """(enabled_path, disabled_path) — first enabled and first @Disabled match."""
    enabled = disabled = None
    for root, _dirs, files in os.walk(test_root):
        for name in sorted(files):
            if not name.endswith(".java"):
                continue
            if not ADAPTER_TEST_RE.search(name[:-len(".java")]):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            if "@Disabled" in text:
                disabled = disabled or path
            else:
                enabled = enabled or path
    return enabled, disabled


def main() -> int:
    parser = argparse.ArgumentParser(
        description="An adapter surface requires an end-to-end adapter test")
    parser.add_argument("--feature-root", required=True)
    parser.add_argument("--test-source-root", default="")
    parser.add_argument("--require-enabled", action="store_true",
                        help="Stage 05: the test must be enabled, not @Disabled")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature_root)

    if not has_adapter_surface(feature_root):
        print("SKIP  no adapter surface declared for this feature")
        return 0

    test_root = args.test_source_root
    if not test_root or not os.path.isdir(test_root):
        print("SKIP  no test source root configured (test.source.root)")
        return 0

    enabled, disabled = find_adapter_tests(test_root)
    if args.require_enabled:
        if enabled:
            print(f"PASS  enabled adapter test present: "
                  f"{os.path.relpath(enabled, test_root)}")
            return 0
        note = " (only @Disabled candidates found)" if disabled else ""
        print("FAIL  adapter surface declared but no ENABLED flow/integration "
              f"test found under {test_root}{note}")
        print("      Stage 05 requires the profile end-to-end test to run green. "
              "Write one from templates/http-integration-test.java and enable it "
              "at 04e-green.")
        return 1

    if enabled or disabled:
        found = enabled or disabled
        state = "enabled" if enabled else "@Disabled (red)"
        print(f"PASS  adapter test present ({state}): "
              f"{os.path.relpath(found, test_root)}")
        return 0

    print("FAIL  adapter surface declared but no flow/integration test found "
          f"under {test_root}")
    print("      Derive a profile-specific end-to-end test (HTTP request -> "
          "adapter -> bootstrap -> concepts/syncs -> response) from "
          "templates/http-integration-test.java. Stage 04c requires it to exist "
          "(it may be @Disabled while red).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
