#!/usr/bin/env python3
"""Generate the Stage 05 trace skeleton (or fill it from observations).

The expected chain per scenario is mechanical from the chain tables. Runtime
evidence and test names come from an optional observations JSON file:

    {"successful-login": {"runtime": ["Web.request[ROUTED]", ...],
                          "test": "LoginFlowTest.successfulLogin"}}

Without observations the runtime/test lines are explicit TODO markers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import artifact_parsers as ap
import chain_paths

SCENARIO_RE = re.compile(
    r"^###\s+Scenario:\s*(.+?)\s*$\n(.*?)(?=^###\s+Scenario:|\Z)",
    re.MULTILINE | re.DOTALL)


def _scenarios(usecase_path):
    text = open(usecase_path, encoding="utf-8").read()
    return [name.strip() for name, _body in SCENARIO_RE.findall(text)]


def _chain_path(chain_dir, name):
    direct = os.path.join(chain_dir, ap.slugify(name) + "-chain.md")
    if os.path.isfile(direct):
        return direct
    for candidate in sorted(os.listdir(chain_dir)):
        if candidate.endswith("-chain.md") and ap.slugify(name) in ap.slugify(candidate):
            return os.path.join(chain_dir, candidate)
    return None


def _expected_chain(rows):
    out = []
    for row in rows:
        if row.then_concept == "Web" and row.then_action == "request":
            out.append("Web.request[ROUTED]")
            continue
        outcome = ap.normalize_outcome(row.outcome_base) if row.outcome_base else ""
        out.append(f"{row.then_concept}/{row.then_action}[{outcome}]")
    return out


def render(feature_root, usecase_path, chain_dir, observations):
    scenarios = _scenarios(usecase_path)
    lines = ["Resume point: <TODO: next feature or iterative change>", ""]
    lines.append(f"# Verification trace — {os.path.basename(feature_root)}")
    lines.append("")
    lines.append("> Stage 05 back-trace from runtime behaviour to use case scenarios.")
    lines.append("")
    for name in scenarios:
        path = _chain_path(chain_dir, name)
        rows = ap.parse_chain_table(path) if path else []
        paths = chain_paths.enumerate_paths(rows)
        if paths:
            success = chain_paths.success_path(paths)
            ordered = ([success] if success else []) + [
                candidate for candidate in paths if candidate is not success]
            for index, branch in enumerate(ordered):
                main = branch is success
                if main:
                    lines.append(f"## {name}")
                else:
                    lines.append(f"### {name} — sub-case: {branch.label}")
                lines.append("")
                lines.append("- **Expected chain (from 01b):**")
                for i, token in enumerate(branch.tokens, 1):
                    lines.append(f"  {i}. `{token}`")
                observed = observations.get(name, {}) if main else {}
                runtime = observed.get("runtime") or ["<TODO: runtime evidence>"]
                lines.append("- **Runtime trace:** " + " -> ".join(
                    f"`{token}`" for token in runtime))
                lines.append(f"- **Flow test:** "
                             f"{observed.get('test', '<TODO: flow test>')}")
                lines.append(f"- **Verdict:** "
                             f"{observed.get('verdict', '<TODO: covered|partial|missing>')}")
                lines.append("")
        else:
            observed = observations.get(name, {})
            lines.append(f"## {name}")
            lines.append("")
            lines.append("- **Expected chain (from 01b):**")
            for i, token in enumerate(_expected_chain(rows), 1):
                lines.append(f"  {i}. `{token}`")
            runtime = observed.get("runtime") or ["<TODO: runtime evidence>"]
            lines.append("- **Runtime trace:** " + " -> ".join(
                f"`{token}`" for token in runtime))
            lines.append(f"- **Flow test:** {observed.get('test', '<TODO: flow test>')}")
            lines.append(f"- **Verdict:** {observed.get('verdict', '<TODO: covered|partial|missing>')}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate Stage 05 trace skeleton")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--observations", default="")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    feature = os.path.abspath(args.feature)
    observations = {}
    if args.observations:
        observations = json.load(open(args.observations, encoding="utf-8"))
    text = render(
        feature,
        os.path.join(feature, "stages", "01_usecase", "output", "usecase.md"),
        os.path.join(feature, "stages", "01b_chain-table", "output"),
        observations)
    out_dir = os.path.join(feature, "stages", "05_verify", "output")
    out_path = os.path.join(out_dir, "trace.md")
    if not args.write:
        sys.stdout.write(text)
        return 0
    if os.path.exists(out_path) and not args.force:
        print(f"FAIL  {out_path} exists — pass --force to overwrite")
        return 1
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"WROTE {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
