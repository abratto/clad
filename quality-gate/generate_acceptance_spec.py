#!/usr/bin/env python3
"""Generate the Acceptance Spec skeleton from the approved use case + chains.

The scenario sections, triggers, token chains, and terminal statuses are
mechanical. Postconditions and the `Test:` bindings still require judgment and
are emitted as explicit placeholders.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import artifact_parsers as ap
import chain_paths
import clad_stages as cs

SCENARIO_RE = re.compile(
    r"^###\s+Scenario:\s*(.+?)\s*$\n(.*?)(?=^###\s+Scenario:|\Z)",
    re.MULTILINE | re.DOTALL)


def _scenarios(usecase_path):
    with open(usecase_path, encoding="utf-8") as handle:
        text = handle.read()
    return [(name.strip(), body) for name, body in SCENARIO_RE.findall(text)]


def _slug(name):
    return ap.slugify(name)


def _chain_path(chain_dir, name):
    direct = os.path.join(chain_dir, _slug(name) + "-chain.md")
    if os.path.isfile(direct):
        return direct
    for candidate in sorted(os.listdir(chain_dir)):
        if candidate.endswith("-chain.md"):
            path = os.path.join(chain_dir, candidate)
            rows = ap.parse_chain_table(path)
            if rows and _slug(name) in _slug(candidate):
                return path
    return None


def _postconditions(body):
    match = re.search(
        r"^- \*\*Postconditions — Success:\*\*\s*$(.*?)(?=^- \*\*|\Z)",
        body, re.MULTILINE | re.DOTALL)
    if not match:
        return "<TODO: postconditions>"
    bullets = []
    current = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            if current:
                bullets.append(" ".join(current))
            current = [stripped[2:].strip()]
        elif stripped and current:
            # Continuation of the current bullet (the use-case bullets wrap).
            current.append(stripped)
    if current:
        bullets.append(" ".join(current))
    return " ".join(b.strip().rstrip(";") for b in bullets) if bullets else "<TODO: postconditions>"


def _token_chain(rows):
    chain = []
    for row in rows:
        if row.then_concept == "Web" and row.then_action == "request":
            chain.append("Web.request[ROUTED]")
            continue
        outcome = ap.normalize_outcome(row.outcome_base) if row.outcome_base else ""
        if row.then_concept and row.then_action:
            chain.append(f"{row.then_concept}.{row.then_action}[{outcome}]")
    return " -> ".join(chain)


def _terminal(rows):
    for row in reversed(rows):
        if (row.then_concept == "Web" and row.then_action == "respond"
                and row.then_suffix):
            status = re.search(r"\d+", row.then_suffix)
            return status.group(0) if status else row.then_suffix.strip("[]")
    return "<TODO: status>"


def _acceptance_tokens(path):
    # The Acceptance Spec uses `Concept.action[...]`; the trace uses `/`.
    return [token.replace("/", ".", 1) for token in path.tokens]


def render(feature_root, usecase_path, chain_dir, title):
    lines = [f"# Acceptance spec — {title}", ""]
    for name, body in _scenarios(usecase_path):
        path = _chain_path(chain_dir, name)
        rows = ap.parse_chain_table(path) if path else []
        trigger = rows[0].when.replace("`", "").strip() if rows else "<TODO: trigger>"
        paths = chain_paths.enumerate_paths(rows)
        if paths:
            success = chain_paths.success_path(paths)
            ordered = ([success] if success else []) + [
                candidate for candidate in paths if candidate is not success]
            for index, branch in enumerate(ordered):
                main = branch is success
                if main:
                    lines.append(f"## Scenario: {name}")
                else:
                    lines.append(f"### Sub-case — {branch.label}")
                lines.append("")
                lines.append(f"- **Trigger:** `{trigger}`")
                lines.append(f"- **Expected response:** `{branch.status}` "
                             f"<TODO: body>")
                lines.append("- **Expected token chain:** " + " -> ".join(
                    f"`{token}`" for token in _acceptance_tokens(branch)))
                lines.append("- **Postconditions:** "
                             + (_postconditions(body) if main
                                else "<TODO: postconditions for this branch>"))
                lines.append("- **Test:** `<TestClass>.<testMethod>`")
                lines.append("")
        else:
            lines.append(f"## Scenario: {name}")
            lines.append("")
            lines.append(f"- **Trigger:** `{trigger}`")
            lines.append(f"- **Expected response:** `{_terminal(rows)}` <TODO: body>")
            lines.append(f"- **Expected token chain:** {_token_chain(rows)}")
            lines.append(f"- **Postconditions:** {_postconditions(body)}")
            lines.append("- **Test:** `<TestClass>.<testMethod>`")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate an Acceptance Spec skeleton")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    feature = os.path.abspath(args.feature)
    usecase = os.path.join(feature, "stages", "01_usecase", "output",
                           "usecase.md")
    chain_dir = cs.CHAIN_DIR(feature)
    out_dir = os.path.join(feature, "stages", "04_implement",
                           "04c_acceptance-tests", "output")
    out_path = os.path.join(out_dir, "acceptance-spec.md")
    title = re.sub(r"^UC-\d+-", "", os.path.basename(feature)).replace("-", " ")
    text = render(feature, usecase, chain_dir, title)
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
