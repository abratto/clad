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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402

import artifact_parsers as ap
import sync_where as sw


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
    r'invoke\(\s*("?)([A-Za-z_][\w.]*)\1\s*,\s*("?)([A-Za-z_][\w.]*)\3')
# Any `conj("name", Concept, action, outcome)` (not only the first after .when).
_CONJ_ANY = re.compile(
    r'conj\(\s*"(\w+)"\s*,\s*("?)([A-Za-z_][\w.]*)\2\s*,'
    r'\s*("?)([A-Za-z_][\w.]*)\4\s*,\s*("?)([A-Za-z_0-9]\w*)\6\s*\)')
# A route matcher literal: `Map.of("route", "login")` / `... lit("login")`.
_ROUTE_LIT = re.compile(r'"route"\s*,\s*(?:lit\(\s*)?"([^"]+)"')
# `invoke(Concept, action, args("name", <factory>(...), ...))`
_INVOKE_ARGS = re.compile(
    r'invoke\(\s*("?)(\w+)\1\s*,\s*("?)(\w+)\3\s*,\s*'
    r'args\(((?:[^()]|\([^()]*\))*)\)', re.DOTALL)
_ARG_NAME = re.compile(r'"(\w+)"\s*,\s*(?:[A-Za-z_]\w*\s*\()')


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


def _parse_dir(sync_dir):
    """`[(SyncSpec, path)]` for every *.sync.md in a directory."""
    out = []
    if not os.path.isdir(sync_dir):
        return out
    for fname in sorted(os.listdir(sync_dir)):
        if not fname.endswith(".sync.md"):
            continue
        path = os.path.join(sync_dir, fname)
        spec = ap.parse_sync(path)
        if spec:
            out.append((spec, path))
    return out


def collect_specs(sync_dir, features_dir):
    specs, failures = [], []
    if sync_dir:
        if os.path.isdir(sync_dir):
            specs.extend(_parse_dir(sync_dir))
        else:
            failures.append((sync_dir, f"sync directory not found: {sync_dir}"))
    if features_dir:
        if os.path.isdir(features_dir):
            for root, _dirs, _files in os.walk(features_dir):
                if "03_syncs/output" in root:
                    specs.extend(_parse_dir(root))
        else:
            failures.append((features_dir, f"features directory not found: {features_dir}"))
    return specs, failures


def spec_route_literals(path):
    """`route: "x"` / `route = "x"` literals in a sync spec's when/where blocks."""
    if not path or not os.path.isfile(path):
        return set()
    text = open(path, encoding="utf-8").read()
    return {f"route={m.group(1)}"
            for m in re.finditer(r'route\s*[:=]\s*"([^"]+)"', text)}


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
                conjunctions = [
                    (symbols.get(m.group(3), m.group(3)),
                     symbols.get(m.group(5), m.group(5)),
                     symbols.get(m.group(7), m.group(7)))
                    for m in _CONJ_ANY.finditer(body)
                ]
                if not conjunctions and concept:
                    conjunctions = [(symbols.get(concept, concept),
                                     symbols.get(action, action),
                                     symbols.get(outcome_raw, outcome_raw) if outcome_raw else "")]
                routes = sorted({f"route={m.group(1)}" for m in _ROUTE_LIT.finditer(body)})
                rules[name] = {
                    "symbols": {k: v for k, v in symbols.items()},
                    "path": path,
                    "trigger": (concept, action, outcome or None),
                    "then_targets": sync_invoke_targets(symbols, body),
                    "conjuncts": conjunctions,
                    "route_literals": routes,
                    "_body": body,
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


def java_invoke_args(body, symbols):
    """`{(concept, action): set(arg names)}` from inline `invoke(...args(...))`."""
    out = {}
    for m in _INVOKE_ARGS.finditer(body):
        concept = symbols.get(m.group(2), m.group(2))
        action = symbols.get(m.group(4), m.group(4))
        out[(concept, action)] = set(_ARG_NAME.findall(m.group(5)))
    return out


def spec_then_args(path):
    """`{(concept, action): set(arg names)}` from a spec's `then { ... }` block."""
    out = {}
    if not path or not os.path.isfile(path):
        return out
    text = open(path, encoding="utf-8").read()
    m = re.search(r"then\s*\{(.*?)\}", text, re.DOTALL)
    if not m:
        return out
    for tm in re.finditer(r"([A-Za-z]+)/([A-Za-z]+)\s*:\s*\[([^\]]*)\]",
                          m.group(1)):
        names = set()
        for arg in tm.group(3).split(";"):
            am = re.match(r"\s*(\w+)\s*:", arg)
            if am:
                names.add(am.group(1))
        out[(tm.group(1), tm.group(2))] = names
    return out


def _conj_set(pairs):
    return {(normalize_token(c), normalize_token(a), normalize_token(o))
            for c, a, o in pairs}


def _target_set(pairs):
    return {(normalize_token(c), normalize_token(a)) for c, a in pairs}


def _route_set(items):
    return {normalize_token(i) for i in items}


def _fmt(items):
    return ", ".join(sorted(str(i) for i in items)) or "<none>"


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--sync-dir", default="", help="Path to one 03_syncs/output directory.")
        parser.add_argument("--features-dir", default="", help="Root features/ tree.")
        parser.add_argument("--sync-impl-dir", required=True, help="Directory of SyncRule Java sources.")
        parser.add_argument("--strict-trigger", action="store_true",
                            help="Also require trigger + primary then target to match Stage 03.")

    def body(args: argparse.Namespace):
        if not args.sync_dir and not args.features_dir:
            print("ERROR: provide --sync-dir or --features-dir.", file=sys.stderr)
            return 1

        specs, failures = collect_specs(args.sync_dir, args.features_dir)
        rules, java_failures = collect_java_syncs(args.sync_impl_dir)
        failures.extend(java_failures)

        for spec, spec_path in specs:
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

            if not args.strict_trigger:
                continue

            # Full parity: EVERY conjunct, EVERY then target, and the route
            # literals must agree. The old check compared only the primary
            # trigger and the first target, so a rule could keep the primary
            # trigger and target while changing its second conjunct, route, or
            # argument sources and still pass (finding 3).
            spec_conjs = _conj_set(
                [(c.concept, c.action, c.outcome) for c in spec.conjuncts])
            impl_conjs = _conj_set(rule.get("conjuncts", []))
            if spec_conjs and not impl_conjs:
                failures.append((label, "unresolved: cannot statically extract the "
                                        "rule's conjuncts to verify parity"))
            elif spec_conjs != impl_conjs:
                failures.append((
                    label, f"conjunct mismatch: spec {_fmt(spec_conjs)} vs "
                           f"impl {_fmt(impl_conjs)}"))

            spec_targets = _target_set(spec.then_targets)
            impl_targets = _target_set(rule.get("then_targets", []))
            if spec_targets and not impl_targets:
                failures.append((label, "unresolved: the rule's `then` has no inline "
                                        "`invoke(...)` target to verify (helper-based "
                                        "targets are unverifiable)"))
            elif spec_targets != impl_targets:
                failures.append((
                    label, f"then-target mismatch: spec {_fmt(spec_targets)} vs "
                           f"impl {_fmt(impl_targets)}"))

            spec_routes = _route_set(spec_route_literals(spec_path))
            impl_routes = _route_set(rule.get("route_literals", []))
            if spec_routes and impl_routes != spec_routes:
                failures.append((
                    label, f"route-literal mismatch: spec {_fmt(spec_routes)} vs "
                           f"impl {_fmt(impl_routes)}"))

            # Argument mapping: the arg names each target receives must agree
            # (the spec's binding VALUES live in prose, so only names are
            # structurally comparable; a renamed/missing arg is a real drift).
            spec_args = spec_then_args(spec_path)
            impl_args = java_invoke_args(body=rule.get("_body", ""),
                                         symbols=rule.get("symbols", {}))
            for key, names in spec_args.items():
                if key in impl_args and impl_args[key] != names:
                    failures.append((
                        label, f"argument mismatch for {key[0]}/{key[1]}: "
                               f"spec {_fmt(names)} vs impl {_fmt(impl_args[key])}"))

            # Binding provenance: the structured `where { ... }` clauses must
            # match the Java `.where(...)` clauses. A spec that declares no
            # `where` block but whose implementation does is UNRESOLVED (the
            # provenance cannot be compared) — not a silent pass.
            try:
                spec_where = sw.spec_where_clauses(
                    open(spec_path, encoding="utf-8").read())
            except sw.WhereParseError as exc:
                failures.append((label, f"malformed `where` block: {exc}"))
                spec_where = None
            impl_where = sw.parse_java_where(
                sw.extract_java_where(rule.get("_body", "")),
                rule.get("symbols", {}))
            if spec_where is None and impl_where:
                failures.append((
                    label, "unresolved: the implementation has `where` clauses "
                           "but the spec declares no `where { ... }` block to "
                           "compare binding provenance against"))
            elif spec_where is not None and \
                    sw.clause_signatures(spec_where) != sw.clause_signatures(impl_where):
                failures.append((
                    label, "where-clause mismatch: spec "
                           f"{_fmt(sw.clause_signatures(spec_where))} vs impl "
                           f"{_fmt(sw.clause_signatures(impl_where))}"))

        if failures:
            print(f"FAIL: {len(failures)} sync implementation parity violation(s):\n")
            for path, message in sorted(failures):
                print(f"  {path}\n    {message}\n")
            print("Every Stage 03 sync contract must lower to one SyncRule.of declaration.")
            return 1

        print(f"PASS  {len(specs)} Stage 03 sync contract(s) have matching SyncRule implementations")
        return 0

    return cr.run_report("Verify every Stage 03 sync has a SyncRule.of implementation", body, argv, configure)



if __name__ == "__main__":
    sys.exit(main())
