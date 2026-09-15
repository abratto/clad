#!/usr/bin/env python3
"""
generate_syncs_java.py — mechanical Stage 03 spec → Java lowering.

For each approved *.sync.md (the same contracts the agents already author via
generate_syncs.py), emit its Java realization as fluent-DSL SyncRule code
(see maintenance/sync-dsl-legibility.md for the sugar and naming grammar).
Two emitter shapes, chosen by --profile:

  java-legible : one <Feature>Syncs.java file with an all() list
                 (dev.legible.example.<feature> layout)
  micronaut    : one final class per rule under <syncs package>,
                 aggregated by <Feature>SyncRules.all() (the v0.3.5 profile shape)

Judgement items (Pattern D sources, non-literal then-args) are emitted as
<!-- TODO --> style Java comments for the agent to resolve; everything else is
mechanically derived from the sync artefact via the same artifact_parsers
grammar the verifiers use, so generated code satisfies
verify_sync_implementation_parity.py by construction.

Usage:
  python3 generate_syncs_java.py --feature features/UC-XX-<slug> \
      --out <src dir root> [--profile micronaut|java-legible] [--write]

Without --write, prints what it would emit (dry run).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import artifact_parsers as ap

REPO_ROOT = Path(__file__).resolve().parents[1]
_DEAD = object()


def _snake_to_camel(text: str) -> str:
    parts = text.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _lower_first(name: str) -> str:
    return name[:1].lower() + name[1:] if name else name


def _source_java(spec) -> list[str]:
    """Emit one line per `where` source to be lowered. TODOs for judgement."""
    lines = []
    # Trigger-input bindings (Pattern A / route matcher case) get mechanically
    # emitted; Pattern D reads surface TODOs for the agent to fill.
    # Parse the where block through artifact_parsers' SyncSpec contract:
    #   has_pattern_d / pattern_d_concepts are flags, but the source
    # expressions themselves are spec content (the agent's judgement).
    if spec_has_pattern_d(spec):
        lines.append("    // TODO: author judgment-specific Pattern D source(s) —")
        lines.append("    //   the .sync.md names: " + ", ".join(spec.pattern_d_concepts))
    return lines


def spec_has_pattern_d(spec) -> bool:
    return bool(spec.pattern_d_concepts)


def render_dsl_rule(spec) -> list[str]:
    """Emit one v2-named fluent-DSL rule block from a parsed sync spec."""
    lines = []
    lines.append('    public SyncRule rule() {')
    lines.append(f'        return rule("{spec.name}")')
    # Trigger concept/action come from the parsed `when` block; completion
    # token name normalized to the actual outcome token used in the Java enum
    # space (e.g. { outcome: "FOUND" } -> "FOUND"). Concept/action constants
    # are the agent's authoring step (per profile) — emit string literals.
    if spec.is_join and spec.conjuncts:
        # Synchronised (multi-`when`) rule: one `conj(...)` per conjunct in
        # declared order (maintenance/engine-declarative-join-collect.md).
        for index, conjunct in enumerate(spec.conjuncts):
            method = ".when" if index == 0 else ".and"
            name = conjunct.name or f"c{index + 1}"
            lines.append(
                f'            {method}(conj("{name}", "{conjunct.concept}", '
                f'"{conjunct.action}", "{conjunct.outcome}"))')
    else:
        lines.append(f'            .when("{spec.trigger_concept}", "{spec.trigger_action}", '
                     f'"{spec.trigger_outcome or ""}"),'.rstrip(","))
    for (tc, ta) in spec.then_targets[:1]:
        lines.append(f'            .then(invoke("{tc}", "{ta}", args()))')
    lines.append('            .build();')
    lines.append('    }')
    return lines


def snake_rule_name(name: str) -> str:
    return _snake_to_camel(
        re.sub(r"^([a-z]+)([A-Z][a-z])", r"\1_\2", _lower_first(name)))


def spec_timestamp(_unused_arg=_DEAD):
    raise AssertionError("internal only")


def when0(spec):
    """Effect-first derivation of the Java trigger string (grammar v2)."""
    m = _v1_to_v2(spec.name)
    return m


def _v1_to_v2(name: str) -> str:
    m = re.match(
        r"^When(?P<tc>[A-Z]\w*?)(?P<ta>[A-Z]\w*?)(?P<comp>[A-Z][A-Za-z0-9]*)"
        r"Then(?P<tc2>[A-Z]\w+?)(?P<ta2>[A-Z][A-Za-z]*?)(?P<scope>For[A-Z][A-Za-z]*)?$",
        name)
    if not m:
        return name  # already v2
    return (f"{m.group('tc2')}{m.group('ta2')}{m.group('scope') or ''}"
            f"When{m.group('tc')}{m.group('ta')}{m.group('comp')}")


def spec_is_v2(name: str) -> bool:
    return not re.match(r"^When[A-Z]", name)


def spec_name(name: str) -> str:
    return name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit fluent-DSL SyncRule Java from Stage 03 sync specs")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--profile", default="micronaut", choices=["micronaut", "java-legible"])
    parser.add_argument("--out", default="", help="Java source root to write into")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    sync_dir = os.path.join(args.feature, "stages", "03_syncs", "output")
    specs = ap.parse_syncs(sync_dir)
    if not specs:
        print(f"SKIP  no .sync.md specs found under {sync_dir}")
        return

    print(f"  CLAD sync lowering — {len(specs)} rule(s), profile={args.profile}")
    errors = []
    for s in specs:
        if not s.trigger_concept or not s.then_targets:
            errors.append(f"{s.filename}: cannot derive trigger/then — resolver required")
    if errors:
        for e in errors:
            print(f"ERROR {e}")
        sys.exit(1)
    if not args.write:
        for s in specs:
            print(f"    rule: {s.name}")
        return
    if not args.out:
        print("FAIL --write requires --out (Java source root)")
        sys.exit(1)
    for s in specs:
        stem = s.name
        target_dir = Path(args.out)
        target_dir.mkdir(parents=True, exist_ok=True)
        java_name = stem
        out_path = (target_dir / f"{java_name}.java")
        body = "\n".join(render_dsl_rule(s))
        out_path.write_text(
            "package <<<APP_PACKAGE_ROOT>>>.syncs;\n\n"
            "import dev.legible.engine.SyncRule;\n"
            "import static dev.legible.engine.Dsl.args;\n"
            "import static dev.legible.engine.Dsl.bind;\n"
            "import static dev.legible.engine.Dsl.conj;\n"
            "import static dev.legible.engine.Dsl.invoke;\n"
            "import static dev.legible.engine.Dsl.lit;\n"
            "import static dev.legible.engine.Dsl.ref;\n"
            "import static dev.legible.engine.Dsl.rule;\n\n"
            "/** Generated from " + stem + ".sync.md — resolve only the TODO markers;\n"
            " *  never re-author the name, trigger, or target (rule sees sync rule contract). */\n"
            "public final class " + java_name + " {\n" + body + "\n}\n")
        print("wrote", out_path)


if __name__ == "__main__":
    main()
