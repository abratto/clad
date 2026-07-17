#!/usr/bin/env python3
"""
verify_step_definition_derivation.py — Stage gate: step-definition bodies
mechanically reference the chain-table rows they were derived from.

Why this exists:
  Stage 04c derives step-definition methods from chain-table rows (one method
  per row, per GHERKIN_INTEGRATION.md rules S1–S3). An agent can write stubs
  that compile but don't exercise the chain table's action sequence.
  `verify_step_definition_parity.py` catches empty stubs; this script catches
  bodies that don't reference the actions they're meant to cover.

  Without this check, step definitions can pass "parity" and "green" checks
  while testing the wrong actions (or testing nothing at all), breaking the
  mechanical trace from use case → chain table → step def → green test.

Checks:
  1. Every business-concept action name in every chain table's "Then" column
     appears in at least one step-definition method body in the glue code.
  2. Coverage is per-feature: each UC's chain-table actions must be covered
     by its own step definitions (or a shared step-def file when multiple
     UCs use one test harness).

Strategy:
  - Parse all `<scenario>-chain.md` files in the chain-table output directory.
    Extract the "Then" column values (e.g., "User.lookupByEmail",
    "PasswordAuth.setPassword", "Session.grant").
  - Strip "Web.respond[...]" entries — these are response assertions, covered
    by generic @Then steps, not business-action step defs.
  - Parse all `.java` files in the glue directory. Extract method body text.
  - For each action name, check if its last component (e.g. "lookupByEmail",
    "createEmailPasswordUser") appears as a substring in any method body.
    Also try the full name (e.g. "User.lookupByEmail").
  - Report every uncovered action name with its source chain-table file.

Usage:
  python3 verify_step_definition_derivation.py \\
    --chain-dir <02b_chain-table/output/> \\
    --glue-dir <src/test/java/com/example/steps/>
"""

import argparse
import os
import re
import sys
import textwrap
from collections import defaultdict


_CHAIN_THEN = re.compile(
    r'\|\s*\d+\s*\|\s*`[^`]+`\s*\|\s*`([^`]+)`\s*\|')
_METHOD_BODY = re.compile(
    r'\b(public|protected|private)\s+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)'
    r'\s*(?:throws\s+\S+\s*)?\{')
_WEB_RESPOND = re.compile(r'^Web\.respond(\[\d+\])?$')


def find_files(root, ext):
    """Recursively find all files with the given extension."""
    result = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(ext):
                result.append(os.path.join(dirpath, f))
    return result


def extract_method_bodies(java_path):
    """Return the concatenated text of all method bodies in a .java file."""
    with open(java_path, encoding='utf-8') as fh:
        text = fh.read()
    bodies = []
    pos = 0
    while True:
        m = _METHOD_BODY.search(text, pos)
        if not m:
            break
        start = m.end()  # right after the opening {
        depth = 0
        end = start - 1
        for i in range(start - 1, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end > start:
            bodies.append(text[start:end])
        pos = end + 1
    return '\n'.join(bodies)


def collect_all_bodies(glue_dir):
    """Return concatenated body text from all .java files in glue_dir."""
    all_text = []
    for jp in find_files(glue_dir, '.java'):
        all_text.append(extract_method_bodies(jp))
    return '\n'.join(all_text)


def extract_action_names(chain_dir):
    """Return {filename: [action_names]} from chain-table .md files.

    Action names are stripped of brackets/branch info — e.g.
    "User.lookupByEmail" stays, "Web.respond[422]" is excluded.
    """
    result = {}
    for cp in find_files(chain_dir, '.md'):
        with open(cp, encoding='utf-8') as fh:
            text = fh.read()
        actions = []
        for m in _CHAIN_THEN.finditer(text):
            full = m.group(1).strip()
            if _WEB_RESPOND.match(full):
                continue  # response assertions — handled by generic @Then steps
            actions.append(full)
        if actions:
            result[os.path.basename(cp)] = actions
    return result


def check_coverage(chain_actions, all_bodies):
    """Return {action_name: [chain_files]} for uncovered actions."""
    all_bodies_lower = all_bodies.lower()
    uncovered = defaultdict(list)
    for fname, actions in chain_actions.items():
        for action in actions:
            # Try the full name first, then the last component
            terms = [action]
            if '.' in action:
                terms.append(action.rsplit('.', 1)[1])
            found = any(t.lower() in all_bodies_lower for t in terms)
            if not found:
                uncovered[f"{action} ({fname})"].append(fname)
    return uncovered


def main():
    parser = argparse.ArgumentParser(
        description="Verify step-def bodies reference chain-table action names")
    parser.add_argument("--chain-dir", required=True,
                        help="Path to 02b_chain-table/output/")
    parser.add_argument("--glue-dir", required=True,
                        help="Path to step-definition Java source directory")
    args = parser.parse_args()

    if not os.path.isdir(args.chain_dir):
        print(f"FAIL  chain-table directory not found: {args.chain_dir}")
        sys.exit(1)

    if not os.path.isdir(args.glue_dir):
        print(f"FAIL  glue directory not found: {args.glue_dir}")
        sys.exit(1)

    chain_actions = extract_action_names(args.chain_dir)
    if not chain_actions:
        print(f"FAIL  no chain-table files found in {args.chain_dir}")
        sys.exit(1)

    all_bodies = collect_all_bodies(args.glue_dir)
    if not all_bodies.strip():
        print(f"FAIL  no method bodies found in glue directory "
              f"{args.glue_dir} — all step definitions are empty stubs")
        print()
        print(textwrap.dedent("""\
            Agent instruction:
              Every step-definition method in the glue code is an empty stub.
              Implement each method so it exercises the application and
              references the chain-table action it was derived from.
              See templates/step-definitions.java and
              methodology/architecture/GHERKIN_INTEGRATION.md for the
              derivation rules (S1–S3).
        """))
        sys.exit(1)

    uncovered = check_coverage(chain_actions, all_bodies)

    total_actions = sum(len(v) for v in chain_actions.values())
    covered = total_actions - len(uncovered)

    print(f"INFO  {covered}/{total_actions} chain-table action(s) covered "
          f"in step-definition bodies")

    if uncovered:
        print(f"FAIL  {len(uncovered)} action(s) not referenced in any "
              f"step-definition method body:")
        for action_name in sorted(uncovered):
            print(f"  - {action_name}")

        print()
        print(textwrap.dedent(f"""\
            Agent instruction:
              Each action above appears in a chain table but is not referenced
              by any step-definition method body. Write step-definition methods
              that exercise these actions. Rule S1 requires one method per
              chain-table row; the method body must reference the action name
              from that row (as a string literal, method call, or assertion).

              For the token-chain assertion step (@Then("the runtime token
              chain matches:")), include these action names in the expected
              token sequence.

              Re-run this script after implementing the missing methods.
        """))
        sys.exit(1)

    print(f"PASS  all {total_actions} chain-table action(s) are covered "
          f"by step-definition method bodies")
    sys.exit(0)


if __name__ == "__main__":
    main()
