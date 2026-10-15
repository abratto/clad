#!/usr/bin/env python3
"""
refresh_stage_contracts.py — re-copy each stage's `## Verify` section from the
feature-skeleton template into a feature's stage `CONTEXT.md`.

Why this exists:
  A feature's stage `CONTEXT.md` is a copy of `templates/feature-skeleton/`
  made when the feature was bootstrapped. When a template's checks change, the
  copy goes stale: the agent follows checks the template no longer names, and
  `advance` runs checks the contract never mentioned (the recurring "stale
  feature-local contract" defect). This copies the `## Verify` section — the
  self-audit the agent runs — from the template, leaving every other section
  (the feature-specific prose) untouched.

Usage:
  python3 refresh_stage_contracts.py --feature features/UC-XX-<slug> [--write]
  python3 refresh_stage_contracts.py --feature features/UC-XX-<slug> --check
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clad_stages as cs  # noqa: E402

_VERIFY_RE = re.compile(r"^##\s+Verify\s*$(.*?)(?=^##\s|\Z)",
                        re.MULTILINE | re.DOTALL)


def verify_section(text: str) -> str:
    match = _VERIFY_RE.search(text)
    return match.group(0) if match else ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh a feature's stage `## Verify` sections from the template")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--template", default="",
                        help="Feature-skeleton root (default: templates/feature-skeleton)")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    feature = os.path.abspath(args.feature)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_root = os.path.abspath(args.template) if args.template else os.path.join(
        repo, "templates", "feature-skeleton")

    stale = []
    for stage in cs.STAGES:
        local = os.path.join(feature, "stages", stage.context_dir, "CONTEXT.md")
        template = os.path.join(template_root, "stages", stage.context_dir, "CONTEXT.md")
        if not (os.path.isfile(local) and os.path.isfile(template)):
            continue
        with open(local, encoding="utf-8") as handle:
            local_text = handle.read()
        with open(template, encoding="utf-8") as handle:
            template_text = handle.read()
        want = verify_section(template_text)
        have = verify_section(local_text)
        if not want or have == want:
            continue
        stale.append((stage, local, local_text, want))

    if not stale:
        print("PASS  every stage `## Verify` section matches the template")
        return 0

    if args.check:
        print(f"STALE  {len(stale)} stage `## Verify` section(s) differ from the "
              f"template — run `./clad refresh-contracts` to refresh:")
        for stage, local, _text, _want in stale:
            print(f"  - {cs.relpath(local, feature)} (stage {stage.id})")
        return 0

    if not args.write:
        print(f"{len(stale)} stage `## Verify` section(s) differ from the template:")
        for stage, local, _text, _want in stale:
            print(f"  - {cs.relpath(local, feature)} (stage {stage.id})")
        print("(dry run — re-run with --write to refresh)")
        return 0

    for _stage, local, local_text, want in stale:
        with open(local, "w", encoding="utf-8") as handle:
            handle.write(_VERIFY_RE.sub(want, local_text, count=1))
    print(f"WROTE  refreshed {len(stale)} stage `## Verify` section(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
