#!/usr/bin/env python3
"""
verify_sync_variable_names.py — Enforce R10: Sync SPARQL variable names

Rule: Sync whereClause() and thenBindings() MUST use ?_when_1 (not ?_w)
for the trigger action node and ?_flow (not ?_f) for the flow token.
Using ?_w or ?_f as synonyms causes flow-token mismatches and runaway
re-firing because SyncAgent.assembleSparql() binds the boilerplate
variables ?_when_1 and ?_flow, and the subclass's variables are
separate SPARQL variables that won't join with the boilerplate.

Request-field variables like ?_slug, ?_token, ?_userId are fine.

Usage:
  python3 verify_sync_variable_names.py [--syncs-dir <path>]

Exits 0 if all syncs comply, 1 otherwise.
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple

# Only these specific shorthands are bugs — they collide with
# the engine's ?_when_1 and ?_flow boilerplate variables.
FORBIDDEN_TRIGGER_SHORTHANDS = {"?_w"}
FORBIDDEN_FLOW_SHORTHANDS = {"?_f"}
SPARQL_VAR_RE = re.compile(r"\?_[a-zA-Z][a-zA-Z0-9_]*")

def extract_method_body(text: str, method_name: str) -> Tuple[Optional[str], Optional[int]]:
    """Extract the body of method_name from Java source text."""
    pattern = re.compile(
        rf"(?:@Override\s*\n\s*)?"
        rf"(?:public\s+|protected\s+)?[\w<>\[\],\s]*\s+{method_name}\s*\([^)]*\)\s*\{{\s*\n?"
        rf"(.*?)\n\s*\}}",
        re.DOTALL
    )
    match = pattern.search(text)
    if not match:
        return None, None
    body = match.group(1)
    line_no = text[:match.start()].count('\n') + 1
    return body, line_no

def check_file(filepath: str) -> List[str]:
    """Check a single sync file. Returns list of violation messages."""
    violations = []
    with open(filepath) as f:
        text = f.read()

    for method in ("whereClause", "thenBindings"):
        body, line = extract_method_body(text, method)
        if body is None:
            continue
        vars_found = set(SPARQL_VAR_RE.findall(body))

        bad_trigger = vars_found & FORBIDDEN_TRIGGER_SHORTHANDS
        bad_flow = vars_found & FORBIDDEN_FLOW_SHORTHANDS

        if bad_trigger:
            violations.append(
                f"  {filepath}:{line}: {method}() uses ?_w instead of ?_when_1 for trigger action"
            )
        if bad_flow:
            violations.append(
                f"  {filepath}:{line}: {method}() uses ?_f instead of ?_flow for flow token"
            )
    return violations

def main():
    syncs_dir = os.environ.get("SYNCS_DIR", None)
    if syncs_dir:
        root = Path(syncs_dir)
    else:
        root = Path(__file__).resolve().parents[1]
        candidates = [
            root / "app" / "backend" / "src" / "main" / "java" / "org" / "clad" / "conduit" / "syncs",
            root / "reference-impl" / "java-micronaut-jena" / "src" / "main" / "java" / "com" / "example" / "app" / "syncs",
        ]
        root = next((c for c in candidates if c.exists()), root)

    if not root.exists():
        print(f"SKIP  Syncs directory not found: {root}")
        sys.exit(0)

    all_violations = []
    for java_file in sorted(root.glob("*.java")):
        violations = check_file(str(java_file))
        all_violations.extend(violations)

    if all_violations:
        print(f"FAIL  R10: {len(all_violations)} sync(s) use forbidden SPARQL variable shorthands")
        for v in all_violations:
            print(v)
        print("\nReplace ?_w with ?_when_1 and ?_f with ?_flow in these syncs.")
        print("See app/backend/CODE_STYLE.md § 'Reserved variable names'")
        sys.exit(1)
    else:
        total = len(list(root.glob("*.java")))
        print(f"PASS  R10: All {total} sync(s) use reserved names (no ?_w or ?_f shorthands)")
        sys.exit(0)

if __name__ == "__main__":
    main()
