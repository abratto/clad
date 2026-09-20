#!/usr/bin/env python3
"""
verify_close_evidence.py — Stage 05 WARN-only close evidence.

Two things Stage 05 promises that no other check enforces:

  1. The canonical trace artefact is `trace.md` (the worked example once wrote
     `verification-trace.md`; both are accepted, the legacy name warns).
  2. When the feature exposes an adapter surface (HTTP/CLI/GraphQL/pub-sub),
     an *enabled* end-to-end adapter test exists (a `*FlowTest` /
     `*IntegrationTest` / `*ContractTest` / `*IT`). A missing one is a real
     gap, but there is no reliable profile-agnostic definition of "the
     adapter test", so this check warns rather than blocks.
  3. A closed feature's RESUME no longer advertises a live stage. The
     `./clad` active-feature heuristic treats any RESUME whose `Current stage`
     names a stage as in progress, so a feature left at `Stage 04c — …` after
     closing can outrank a genuinely live one — and a command that writes (for
     example promotion, which replaces corpus entries) can then target the
     stale feature and overwrite newer content with its older proposal.

Exit is always 0 — this is a review aid, not a gate.
"""

import argparse
import os
import re
import sys


ADAPTER_TEST_RE = re.compile(r"(?:Flow|Integration|Contract|IT)Test?$|IT$")


def has_adapter_surface(feature_root):
    chain_dir = os.path.join(feature_root, "stages", "01b_chain-table", "output")
    if os.path.isdir(chain_dir):
        for name in sorted(os.listdir(chain_dir)):
            if not name.endswith(".md") or name.endswith("-all-scenarios-chain.md"):
                continue
            with open(os.path.join(chain_dir, name), encoding="utf-8",
                      errors="replace") as handle:
                if re.search(r"Web[/.](?:request|handle|respond)", handle.read()):
                    return True
    usecase = os.path.join(feature_root, "stages", "01_usecase", "output",
                           "usecase.md")
    if os.path.isfile(usecase):
        with open(usecase, encoding="utf-8", errors="replace") as handle:
            return bool(re.search(r"\bWeb\b", handle.read()))
    return False


def find_enabled_adapter_test(test_root):
    if not test_root or not os.path.isdir(test_root):
        return None, False
    disabled_seen = False
    for root, _dirs, files in os.walk(test_root):
        for name in sorted(files):
            if not name.endswith(".java"):
                continue
            stem = name[:-len(".java")]
            if not ADAPTER_TEST_RE.search(stem):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            if "@Disabled" in text:
                disabled_seen = True
                continue
            return path, disabled_seen
    return None, disabled_seen


CURRENT_STAGE_RE = re.compile(r"^\s*-\s*\*\*Current stage:\*\*\s*`([^`]*)`", re.M)
CLOSED_STAGE_RE = re.compile(r"^\s*(?:None|TBD)\b|feature complete", re.I)


def read_current_stage(feature_root):
    """The value of RESUME.md's `Current stage` line, or None."""
    path = os.path.join(feature_root, "RESUME.md")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as handle:
        match = CURRENT_STAGE_RE.search(handle.read())
    return match.group(1).strip() if match else None


def main():
    parser = argparse.ArgumentParser(description="Stage 05 close-evidence warnings")
    parser.add_argument("--feature-root", required=True)
    parser.add_argument("--test-source-root", default="")
    args = parser.parse_args()

    feature_root = os.path.abspath(args.feature_root)
    out_dir = os.path.join(feature_root, "stages", "05_verify", "output")
    warnings = []

    canonical = os.path.join(out_dir, "trace.md")
    legacy = os.path.join(out_dir, "verification-trace.md")
    if not os.path.isfile(canonical):
        if os.path.isfile(legacy):
            warnings.append(
                "Stage 05 uses the legacy name 'verification-trace.md'; the "
                "canonical contract is 'trace.md'.")
        elif os.path.isdir(out_dir):
            warnings.append("Stage 05 output has no 'trace.md'.")

    if has_adapter_surface(feature_root):
        found, disabled_seen = find_enabled_adapter_test(args.test_source_root)
        if found:
            print(f"PASS  adapter integration test present: "
                  f"{os.path.relpath(found, feature_root)}")
        else:
            note = " (only @Disabled candidates found)" if disabled_seen else ""
            warnings.append(
                "adapter surface declared but no enabled flow/integration test "
                f"found under {args.test_source_root or '<unset>'}{note}.")

    # A closed feature (trace.md written) must not still advertise a live stage.
    if os.path.isfile(canonical):
        stage = read_current_stage(feature_root)
        if stage and not CLOSED_STAGE_RE.search(stage):
            warnings.append(
                f"RESUME.md still says 'Current stage: {stage}' although the "
                "feature is closed; set it to 'None — feature complete' so the "
                "active-feature heuristic cannot pick this feature over a live "
                "one (a write command may otherwise target it).")

    for warning in warnings:
        print(f"WARN  {warning}")
    if not warnings:
        print("PASS  Stage 05 close evidence present")
    sys.exit(0)


if __name__ == "__main__":
    main()
