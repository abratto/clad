#!/usr/bin/env python3
"""Require governed maintenance records for engine and profile changes."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
MAINTENANCE_DIR = REPO_ROOT / "maintenance"
MAINTENANCE_PATTERNS = (
    re.compile(r"^reference-impl/[^/]+/src/(main|test)/.+/engine/.*\.(java|kt|scala|py|ts|js)$"),
    re.compile(r"^reference-impl/[^/]+/(Dockerfile|docker-compose[^/]*\.(yml|yaml))$"),
    re.compile(r"^reference-impl/[^/]+/src/main/resources/.*"),
    re.compile(r"^clad\.properties$"),
    # The canonical concept corpus is system-scope: no single feature owns it, so
    # an edit no feature's `_changes/` record can carry (R22's current-source rule
    # for a feature that is no longer the source) is governed by the maintenance
    # route. This is the route R22/CONCEPTS.md already names for that case.
    re.compile(r"^features/_system/concepts/[^/]+\.(concept|data-model|contract)\.md$"),
)

# `clad.properties` is a platform-config surface for CLAD itself, but it is ALSO
# the file a derived project edits to point CLAD at its own code. A change that
# only edits these derived-project binding keys is project configuration, not a
# platform change, and must not require a maintenance record (experiment defect
# D1: the first thing a downstream project does was blocked).
PROJECT_CONFIG_KEYS = {
    "test.command",
    "sync.impl.dir",
    "concept.impl.dir",
    "test.source.root",
    "concepts.dir",
    "storage.layer",
}


def git_names(args):
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    return result.stdout.splitlines() if result.returncode == 0 else []


def changed_files(base, changed_files_file):
    if changed_files_file:
        return [line.strip() for line in Path(changed_files_file).read_text().splitlines() if line.strip()]
    names = set(git_names(["git", "diff", "--name-only", f"{base}...HEAD"]))
    names.update(git_names(["git", "diff", "--name-only", "--cached"]))
    return sorted(names)


def is_maintenance_scope(path):
    return any(pattern.match(path) for pattern in MAINTENANCE_PATTERNS)


def changed_property_keys(diff_text):
    """Keys assigned on added/removed `key=value` lines of a clad.properties diff."""
    keys = set()
    for line in diff_text.splitlines():
        if not (line.startswith("+") or line.startswith("-")):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        content = line[1:].strip()
        if not content or content.startswith("#") or "=" not in content:
            continue
        keys.add(content.split("=", 1)[0].strip())
    return keys


def clad_properties_diff(path, base):
    """Unified diff for `path` across the committed-on-branch and staged surfaces."""
    parts = []
    for surface in (
        ["git", "diff", "--unified=0", f"{base}...HEAD", "--", path],
        ["git", "diff", "--unified=0", "--cached", "--", path],
    ):
        parts.extend(git_names(surface))
    return "\n".join(parts)


def is_project_config_only(diff_text):
    """True when a clad.properties diff only edits derived-project binding keys."""
    keys = changed_property_keys(diff_text)
    return bool(keys) and keys <= PROJECT_CONFIG_KEYS


def field_value(text, label):
    """The backticked value of a `- **Label:** `value`` line.

    The shipped template wraps a field's parenthetical explanation onto later
    lines (e.g. `Status: \`active\` (\`draft\` until …)`), so the value must be
    read as the first backticked token — not anchored to end-of-line, which
    would silently fail to parse the template's own format.
    """
    match = re.search(rf"^- \*\*{re.escape(label)}:\*\*\s*`([^`\n]+)`", text, re.MULTILINE)
    return match.group(1).strip().lower() if match else ""


def active_records():
    if not MAINTENANCE_DIR.is_dir():
        return []
    records = []
    for path in sorted(MAINTENANCE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if field_value(text, "Status") == "active":
            records.append((path, text))
    return records


def has_passing_test(text):
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[3] == "pass":
                return True
    return False


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--base", default="origin/main")
        parser.add_argument("--changed-files-file", default="")
        parser.add_argument("--require-evidence", action="store_true")

    def body(args: argparse.Namespace) -> cr.Verdict:
        scoped = [path for path in changed_files(args.base, args.changed_files_file) if is_maintenance_scope(path)]
        # A derived project editing only its own binding keys is project config, not
        # a platform change (D1). A clad.properties-only diff on those keys drops out.
        if not args.changed_files_file and scoped == ["clad.properties"]:
            if is_project_config_only(clad_properties_diff("clad.properties", args.base)):
                return cr.Verdict.ok(
                    "clad.properties binding-key change is project configuration, "
                    "not a platform change")
        if not scoped:
            return cr.Verdict.ok(
                "no engine, profile, configuration, or deployment changes detected")

        records = active_records()
        if len(records) != 1:
            return cr.Verdict.fail(
                "maintenance-scoped changes require exactly one active "
                "maintenance/<change-name>.md record")

        path, text = records[0]
        failures = []
        if field_value(text, "Change class") not in {"platform", "mixed"}:
            failures.append("missing or invalid Change class")
        if field_value(text, "Feature-contract impact") not in {"preserved", "re-entered"}:
            failures.append("missing or invalid Feature-contract impact")
        if field_value(text, "Design gate") != "approved":
            failures.append("design gate is not approved")
        if "## Contract impact" not in text or "## Impact matrix" not in text or "## Test matrix" not in text:
            failures.append("missing required impact or test-matrix section")
        if args.require_evidence:
            if field_value(text, "Evidence gate") != "approved":
                failures.append("evidence gate is not approved")
            if not has_passing_test(text):
                failures.append("test matrix has no passing test evidence")

        if failures:
            return cr.Verdict.fail(
                f"maintenance record {path.relative_to(REPO_ROOT)}", [
                    cr.Problem(failure) for failure in failures])

        return cr.Verdict.ok(
            f"maintenance change governed by {path.relative_to(REPO_ROOT)}")

    return cr.run_check(
        "Verify maintenance-change governance.", body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
