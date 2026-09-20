#!/usr/bin/env python3
"""
verify_sync_implementation_parity.py — every Stage 03 sync has a matching
`SyncRule.of(...)` implementation.

Checks:
  1. Every `*.sync.md` under `--sync-dir` (or `--features-dir`) has a matching
     `SyncRule.of("<Name>", ...)` declaration under `--sync-impl-dir`.
  2. With `--strict-trigger`, the declaration's trigger concept/action/outcome
     (and primary inline `then` target) must match the Stage 03 contract.

Sync specs are parsed by the shared `artifact_parsers` grammar, so this check
and the generators cannot drift. The legacy `SyncAgent`/SPARQL profile was
retired (see `reference-impl/LEGACY.md`).

Usage:
  python3 verify_sync_implementation_parity.py \
    --sync-dir features/UC-XX/stages/03_syncs/output \
    --sync-impl-dir reference-impl/java-legible/src/main/java/dev/legible/example/<feature> \
    [--strict-trigger]
"""

import argparse
import os
import re
import sys

import artifact_parsers as ap


SYNC_SUFFIX = ".sync.md"
# Any rule declaration head: legacy `SyncRule.of("Name", ...)`, joined
# `SyncRule.ofJoin("Name", ...)`, or fluent `rule("Name")`.
_RULE_HEAD = re.compile(r'(?:SyncRule\.ofJoin|SyncRule\.of|rule)\(\s*"(\w+)"')
# Legacy positional shape: SyncRule.of("Name", "concept", "action", "outcome", ...)
_SYNC_RULE_OF_HEAD = re.compile(
    r'SyncRule\.of\(\s*"(\w+)"\s*,\s*"(\w+)"\s*,\s*"(\w+)"\s*,\s*"([^"]*)"')
# Fluent DSL shape (see maintenance/sync-dsl-legibility.md):
#   rule("Name")\n .when("Concept", "action"[, "outcome"]) [optional .matching(...)]
_DSL_RULE_HEAD = re.compile(
    r'rule\(\s*"(\w+)"\s*\)(?:.{0,400}?)\.when\(\s*("?)([A-Za-z_][\w.]*)\2\s*,\s*"?([A-Za-z_][\w.]*)"?(?:\s*,\s*"?([A-Za-z_0-9]\w*)"?)?\s*\)',
    re.DOTALL)
# Joined DSL conjunct (the primary is the first): conj("name", "Concept", "action",
# "outcome"). Concept and action may be quoted literals or the concept/action
# CONSTANTS the DSL prefers — a rule whose own trigger is a conjunct (which is
# what a flow pin makes it) is written with constants.
_CONJ_HEAD = re.compile(
    r'\.when\(\s*conj\(\s*"(\w+)"\s*,\s*("?)([A-Za-z_][\w.]*)\2\s*,'
    r'\s*("?)([A-Za-z_][\w.]*)\4\s*,\s*("?)([A-Za-z_0-9]\w*)\6\s*\)')
_SYNC_RULE_INVOKE = re.compile(
    r'invoke\(\s*("?)([A-Za-z_]\w*)\1\s*,\s*("?)([A-Za-z_]\w*)\3')


def sync_invoke_targets(symbols, text):
    return [(symbols.get(c, c), symbols.get(a, a))
            for m in _SYNC_RULE_INVOKE.finditer(text)
            for c, a in [(m.group(2), m.group(4))]]


def symbol_table(package_dir):
    """Resolve `public static final String <ID> = <value>;` constants found
    under a package directory so `.when(WEB, REQUEST, "routed")`-style
    constant references resolve to literal values. Chained values
    (`String WEB = WebConcept.NAME;`) resolve transitively through the
    qualified map (see maintenance/sync-dsl-legibility.md)."""
    literals = {}        # Class.CONST -> literal
    simple = {}          # CONST -> (literal | qualified ref)
    if not package_dir or not os.path.isdir(package_dir):
        return table_out(literals, simple)
    const_re = re.compile(r'String\s+([A-Z][A-Z0-9_]+)\s*=\s*("?)([A-Za-z0-9_."]+)\2;')
    for root, _, files in os.walk(package_dir):
        class_name = None
        for fn in files:
            if not fn.endswith(".java"):
                continue
            path = os.path.join(root, fn)
            text = open(path, encoding="utf-8").read()
            cm = re.search(r'(?:final class|class)\s+([A-Za-z_]\w*)', text)
            cname = cm.group(1) if cm else fn[:-5]
            for m in const_re.finditer(text):
                key = f"{cm.group(1) if cm else fn[:-5]}.{m.group(1)}"
                literals.setdefault(key, m.group(3))
                simple.setdefault(m.group(1), m.group(3))
    table = {}
    for ident, value in simple.items():
        if value in literals:
            table[ident] = literals[value]
        elif re.match(r"^[A-Za-z_]\w*\.[A-Z]", value):
            table[ident] = literals.get(value, value)
        else:
            table[ident] = value
    for qual, literal in dict(literals).items():
        table.setdefault(qual, literal)
    return table


def normalize_token(raw):
    return re.sub(r"[^a-z0-9]", "", (raw or "").strip().lower())


def collect_specs(sync_dir, features_dir):
    specs, failures = [], []
    if sync_dir:
        if os.path.isdir(sync_dir):
            specs.extend(ap.parse_syncs(sync_dir))
        else:
            failures.append((sync_dir, f"sync directory not found: {sync_dir}"))
    if features_dir:
        if os.path.isdir(features_dir):
            for root, _dirs, _files in os.walk(features_dir):
                if "03_syncs/output" in root:
                    specs.extend(ap.parse_syncs(root))
        else:
            failures.append((features_dir, f"features directory not found: {features_dir}"))
    return specs, failures


def collect_java_syncs(sync_impl_dir):
    if not os.path.isdir(sync_impl_dir):
        return {}, [(sync_impl_dir, f"sync implementation directory not found: {sync_impl_dir}")]
    rules = {}
    for root, _dirs, files in os.walk(sync_impl_dir):
        for filename in sorted(files):
            if not filename.endswith(".java"):
                continue
            path = os.path.join(root, filename)
            text = open(path, encoding="utf-8").read()
            heads = [(m.start(), m.group(1)) for m in _RULE_HEAD.finditer(text)]
            heads.sort()
            # Constants may live in sibling concept classes — walk module root.
            module_root = path
            for _ in range(2):
                module_root = os.path.dirname(module_root)
            symbols = symbol_table(module_root)
            for index, (start, name) in enumerate(heads):
                end = heads[index + 1][0] if index + 1 < len(heads) else len(text)
                body = text[start:end]
                concept = action = outcome_raw = None
                m_of = _SYNC_RULE_OF_HEAD.match(body)
                m_join = _CONJ_HEAD.search(body)
                m_dsl = _DSL_RULE_HEAD.search(body)
                if m_of:
                    concept, action, outcome_raw = m_of.group(2), m_of.group(3), m_of.group(4)
                elif m_dsl:
                    # The classic primary first: a pinned rule's PRIMARY is its own
                    # trigger, and only a real join has a `conj(...)` primary.
                    concept, action = m_dsl.group(3), m_dsl.group(4)
                    outcome_raw = m_dsl.group(5)
                elif m_join:
                    concept = m_join.group(3)
                    action = m_join.group(5)
                    outcome_raw = m_join.group(7)

                outcome = symbols.get(outcome_raw, outcome_raw) if outcome_raw else ""
                rules[name] = {
                    "symbols": {k: v for k, v in symbols.items()},
                    "path": path,
                    "trigger": (concept, action, outcome or None),
                    "then_targets": sync_invoke_targets(symbols, body),
                }
    return rules, []


def _deref(symbol, symbols):
    return symbols.get(symbol, symbol)


def trigger_matches(spec, trigger):
    if not trigger:
        return False
    concept, action, outcome = trigger
    return (
        normalize_token(concept) == normalize_token(spec.trigger_concept)
        and normalize_token(action) == normalize_token(spec.trigger_action)
        and normalize_token(outcome) == normalize_token(spec.trigger_outcome)
    )


def then_matches(spec, targets):
    """True if the rule's inline `then` target(s) include the spec's target.
    A rule whose `then` uses a helper (no inline `invoke(...)`) is
    unverifiable here and passes — only positive evidence of a mismatch fails."""
    if not targets or not spec.then_targets:
        return True
    tc, ta = spec.then_targets[0]
    return any(
        normalize_token(c) == normalize_token(tc)
        and normalize_token(a) == normalize_token(ta)
        for c, a in targets
    )


def main():
    parser = argparse.ArgumentParser(
        description="Verify every Stage 03 sync has a SyncRule.of implementation")
    parser.add_argument("--sync-dir", default="", help="Path to one 03_syncs/output directory.")
    parser.add_argument("--features-dir", default="", help="Root features/ tree.")
    parser.add_argument("--sync-impl-dir", required=True, help="Directory of SyncRule Java sources.")
    parser.add_argument("--strict-trigger", action="store_true",
                        help="Also require trigger + primary then target to match Stage 03.")
    args = parser.parse_args()

    if not args.sync_dir and not args.features_dir:
        print("ERROR: provide --sync-dir or --features-dir.", file=sys.stderr)
        sys.exit(1)

    specs, failures = collect_specs(args.sync_dir, args.features_dir)
    rules, java_failures = collect_java_syncs(args.sync_impl_dir)
    failures.extend(java_failures)

    for spec in specs:
        rule = rules.get(spec.name)
        label = f"{spec.filename} ({spec.name})"
        if not rule:
            failures.append((label, "no matching SyncRule.of declaration found"))
            continue
        if args.strict_trigger and not trigger_matches(
                spec,
                tuple(_deref(x, rule.get("symbols", {})) for x in rule["trigger"])):
            c, a, o = rule["trigger"]
            failures.append((
                label, f"trigger mismatch: expected "
                       f"{spec.trigger_concept}/{spec.trigger_action}[{spec.trigger_outcome}], "
                       f"found {c}/{a}[{o}]"))
        if args.strict_trigger and spec.then_targets and not then_matches(spec, rule["then_targets"]):
            tc, ta = spec.then_targets[0]
            failures.append((label, f"then mismatch: expected {tc}/{ta}, "
                                    f"found {rule['then_targets']}"))

    if failures:
        print(f"FAIL: {len(failures)} sync implementation parity violation(s):\n")
        for path, message in sorted(failures):
            print(f"  {path}\n    {message}\n")
        print("Every Stage 03 sync contract must lower to one SyncRule.of declaration.")
        sys.exit(1)

    print(f"PASS  {len(specs)} Stage 03 sync contract(s) have matching SyncRule implementations")
    sys.exit(0)


if __name__ == "__main__":
    main()
