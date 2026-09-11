#!/usr/bin/env python3
"""
verify_action_log_isolation.py — Gate: concept state is reached only through
the engine.

Canonical (fire-after-commit) check for R4: no class outside `engine/` and the
`*Concept` / `*App` / `*Syncs` wiring may call `FactStore`/`Region` methods
directly (`region`, `write`, `read`, `subjects`, `facts`, ...). A controller or
service that reaches into a concept's region is doing business coordination
the syncs should own, and breaking the flow-token traceability chain.

The legacy Jena `ActionLog`/SPARQL variant was retired with that profile (see
`reference-impl/LEGACY.md`).

Usage:
    python3 verify_action_log_isolation.py --app-source-root <path>
    python3 verify_action_log_isolation.py   # derives from concept.impl.dir
"""

import argparse
import os
import re
import sys
from pathlib import Path


# Direct store/region method calls. `region`/`Region` as a receiver catches a
# concept that reaches outside its own `region` field, or a non-concept class
# that obtained a Region.
_STORE_ACCESS = re.compile(
    r'\b(?:factStore|FactStore|region|Region)\s*\.\s*'
    r'(?:region|getRegion|write|read|remove|clear|subjects|facts|'
    r'all|query|delete|put)\s*\('
)
_ALLOWED = re.compile(r'(?:Concept|App|Syncs)\.java$')
_WAIVER = re.compile(r'CLAD:\s*(?:ActionLog|store)\s+waiver\s*[—-]', re.IGNORECASE)


def strip_comments_and_strings(source):
    """Strip Java comments and string literals before matching."""
    s = re.sub(r'/\*.*?\*/', ' ', source, flags=re.DOTALL)
    s = re.sub(r'(?<!:)//.*$', ' ', s, flags=re.MULTILINE)
    s = re.sub(r'"""(?:\\.|[^"])*?"""', ' ', s)
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    return s


def read_clad_property(key, default=""):
    d = Path.cwd().resolve()
    while True:
        candidate = d / "clad.properties"
        if candidate.is_file():
            with open(candidate) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    if k.strip() == key:
                        val = v.strip()
                        return val.split("  #")[0].rstrip() if "  #" in val else val
            return default
        parent = d.parent
        if parent == d:
            return default
        d = parent


def main():
    parser = argparse.ArgumentParser(
        description="Verify FactStore/Region access is isolated to concepts and engine")
    parser.add_argument("--app-source-root", default=None,
                        help="Root package containing the concepts/engine sources")
    args = parser.parse_args()

    app_root = args.app_source_root
    if not app_root:
        concept_dir = read_clad_property("concept.impl.dir", "")
        if concept_dir:
            app_root = str(Path(concept_dir).parent)
        else:
            print("FAIL  could not determine app source root. "
                  "Set concept.impl.dir in clad.properties or pass --app-source-root.")
            sys.exit(1)
    app_root = os.path.abspath(app_root)
    if not os.path.isdir(app_root):
        print(f"FAIL  app source root not found: {app_root}")
        sys.exit(1)

    sources = [p for p in sorted(Path(app_root).rglob("*.java"))
               if "engine" not in p.parts]
    has_store = any("FactStore" in p.read_text(errors="ignore") for p in sources)
    if not has_store:
        print(f"WARN  store isolation not evaluated for {app_root} — no "
              f"FactStore wiring found. Review R4 manually.")
        sys.exit(0)

    violations = []
    checked = 0
    for p in sources:
        if _ALLOWED.search(str(p)) or "engine" in p.parts:
            continue
        source = p.read_text(errors="ignore")
        if _WAIVER.search(source):
            continue
        text = strip_comments_and_strings(source)
        checked += 1
        for m in _STORE_ACCESS.finditer(text):
            violations.append((str(p.relative_to(app_root)),
                               text[:m.start()].count("\n") + 1, m.group(0)))

    if violations:
        print(f"FAIL  {len(violations)} direct FactStore/Region access "
              f"violation(s) outside engine/concepts (R4):")
        for rel, lineno, call in violations:
            print(f"    {rel}:{lineno}: {call}...")
        print("  Only concepts own a Region; coordination belongs in syncs.")
        sys.exit(1)

    if checked == 0:
        print("WARN  store isolation not evaluated: no non-engine, non-concept "
              "source files to inspect (expected only for a very small app).")
    else:
        print(f"PASS  store isolation: {checked} non-engine file(s) avoid "
              f"direct FactStore/Region access")
    sys.exit(0)


if __name__ == "__main__":
    main()
