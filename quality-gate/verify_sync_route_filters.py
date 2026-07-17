#!/usr/bin/env python3
"""
verify_sync_route_filters.py — Enforce R11: Route filtering on shared-concept syncs

Rule: Every sync that fires on a business-concept action (NOT Web/request)
and writes Web/respond MUST include a route filter in its whereClause().
Without this, a sync like LoginRespondSuccess will fire for register flows
too, producing wrong HTTP status codes.

Usage:
  python3 verify_sync_route_filters.py [--sync-impl-dir <path>]

Exits 0 if all applicable syncs comply, 1 otherwise.
"""

import argparse
import re
import sys
import os
from pathlib import Path
from typing import List, Optional

def extract_method_body(text: str, method_name: str) -> Optional[str]:
    pattern = re.compile(
        rf"(?:@Override\s*\n\s*)?"
        rf"(?:public\s+|protected\s+)?[\w<>\[\],\s]*\s+{method_name}\s*\([^)]*\)\s*\{{\s*\n?"
        rf"(.*?)\n\s*\}}",
        re.DOTALL
    )
    match = pattern.search(text)
    return match.group(1) if match else None

def find_line_no(text: str, pos: int) -> int:
    return text[:pos].count('\n') + 1

# Actions that are shared across multiple flows — cross-flow collision is real.
# Only these trigger actions require a mandatory route filter guard.
SHARED_ACTIONS = {
    "Session/lookup",       # profile, update-profile, create-article, update-article,
                            # delete-article, add-comment, delete-comment, favorite,
                            # unfavorite, follow, unfollow, feed
    "Session/grant",        # login, signin, register
    "PasswordAuth/check",   # login, signin
    "Article/list",         # browse-all, browse-by-tag, browse-by-author
    "User/lookupByUsername",# view-profile, follow, unfollow
}

def extract_trigger_action(text: str) -> Optional[str]:
    """Extract the concept/action that triggers this sync."""
    match = re.search(r'SyncTrigger\s*\(\s*(?:([\w.]+)\.)?([\w.]+\.IRI|FlowManager\.\w+)\s*,\s*"([^"]+)"', text)
    if not match:
        return None
    concept_class = match.group(2) or ""
    action_name = match.group(3) or ""
    # Map class constants to short names
    concept_map = {
        "SessionConcept.IRI": "Session",
        "ArticleConcept.IRI": "Article",
        "UserConcept.IRI": "User",
        "CommentConcept.IRI": "Comment",
        "PasswordAuthConcept.IRI": "PasswordAuth",
        "FavoriteConcept.IRI": "Favorite",
        "FollowConcept.IRI": "Follow",
    }
    concept = concept_map.get(concept_class, concept_class.replace(".IRI", ""))
    return f"{concept}/{action_name}"

def check_file(filepath: str) -> List[str]:
    violations = []
    with open(filepath) as f:
        text = f.read()

    trigger_action = extract_trigger_action(text)
    if not trigger_action:
        return []

    # Only check shared actions — single-flow actions don't need route filters
    if trigger_action not in SHARED_ACTIONS:
        return []

    # If it's a Web/request trigger, no route filter needed
    if "Web/request" in trigger_action or "WEB_CONCEPT_IRI" in text.split("trigger()")[1].split(";")[0][:100]:
        return []

    # Check if thenBindings writes Web/respond
    then_body = extract_method_body(text, "thenBindings")
    if not then_body:
        return []

    writes_web_respond = bool(re.search(
        r'concept\s+<.*?/concept/web\s*>',
        then_body
    ))
    metadata_match = re.search(r'fires\s*=\s*"Web/respond', text)
    writes_web_respond = writes_web_respond or (metadata_match is not None)

    if not writes_web_respond:
        return []

    # This sync fires on a business concept and writes Web/respond.
    # Check for route filter in whereClause
    where_body = extract_method_body(text, "whereClause")
    if not where_body:
        return []

    has_route_filter = re.search(r':route\s+\?_route', where_body) is not None
    has_parameterize = bool(re.search(r'bindLiteral\s*\(\s*(?:\w+\s*,\s*)?\"_route\"', text))
    has_param = bool(re.search(r'parameterizeSparql\s*\(\s*String\s+\w+\s*\)\s*\{', text))

    if not has_route_filter:
        class_name = re.search(r'class\s+(\w+)', text)
        name = class_name.group(1) if class_name else os.path.basename(filepath)
        violations.append(
            f"  {filepath}: {name} — fires on business concept, writes Web/respond, "
            f"but whereClause() has no :route ?_route guard"
        )
    return violations

def main():
    parser = argparse.ArgumentParser(
        description="Verify business-concept syncs have route filters (R11)")
    parser.add_argument("--sync-impl-dir", default="",
                        help="Directory containing SyncAgent Java implementations")
    args = parser.parse_args()

    if args.sync_impl_dir and os.path.isdir(args.sync_impl_dir):
        root = Path(args.sync_impl_dir)
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
        print(f"FAIL  R11: {len(all_violations)} business-concept sync(s) missing route filter")
        for v in all_violations:
            print(v)
        print("\nEvery sync that fires on a business concept and writes Web/respond")
        print("MUST include :route ?_route in whereClause().")
        print("See app/backend/CODE_STYLE.md § 'Must filter by route'")
        sys.exit(1)
    else:
        total = len(list(root.glob("*.java")))
        print(f"PASS  R11: All applicable business-concept syncs have route filters ({total} files scanned)")
        sys.exit(0)

if __name__ == "__main__":
    main()
