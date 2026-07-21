#!/usr/bin/env python3
"""
verify_action_log_isolation.py — Gate: only concepts and the engine may access
the ActionLog directly.

Why this exists:
    CLAD architecture rule R4 requires the infrastructure layer (controllers,
    HTTP entry points) to be transport-only: normalize input, invoke the flow
    root via engine.FlowManager.rootAction(), await the response via
    SyncDispatcher.awaitResponse(), and translate output. Infrastructure must
    not bypass the engine to read or write concept state directly.

    When a controller calls actionLog.select() or actionLog.update() with raw
    SPARQL against a concept graph, it:
    - Violates R4 (infrastructure becomes a business-coordination layer)
    - Breaks WYSIWID legibility (no artefact documents what the controller does)
    - Bypasses the flow-token chain (Stage 05 back-trace can't see these writes)
    - Creates hidden coupling between controllers and concept internals

    This check was motivated by a real CLAD project where an agent implemented
    48 raw SPARQL queries inside controllers to make tests pass, creating
    undocumented, untraceable business logic in the transport layer.

Checks:
    1. No file under infrastructure/ contains direct ActionLog method calls
       (select, update, getDataset, execute, etc.) — these belong in concepts
       and the engine.
    2. No file outside concepts/ and engine/ contains concept graph name
       literals (GRAPH <concept:...>) — controllers should not know concept
       graph URIs or action names.

Usage:
    python3 verify_action_log_isolation.py --app-source-root <path>
    python3 verify_action_log_isolation.py  # reads concept.impl.dir + falls back

Wired into: Stage 04d or 04e checks (implementation-level). This is a
profile-agnostic check that scans Java/Kotlin source files.
"""

import argparse
import os
import re
import sys
from pathlib import Path


# Patterns that indicate direct ActionLog access
_ACTION_LOG_DIRECT_ACCESS = re.compile(
    r'\b(actionLog|log)\s*\.\s*(select|update|getDataset|execute|delete|'
    r'insert|add|remove|contains|listSubjects|listObjects|'
    r'getBaseModel|query|createModel)'
    r'\s*\('
)

# Patterns that indicate concept graph knowledge in non-concept code
_CONCEPT_GRAPH_LITERAL = re.compile(
    r'GRAPH\s+<?(?:concept:|\w+Concept\.\w+)'
    r'|:concept\s+<?\w+'
    r'|:name\s+"(?!request|respond)"'  # Web concept uses "request"/"respond"
)

# Patterns that indicate engine bypass — controller doing business work
_ENGINE_BYPASS_PATTERNS = re.compile(
    r'\b(flowManager|syncDispatcher)\s*\.\s*'
    r'(?!rootAction|awaitResponse|get)',
)


# Pattern that waives a file from ActionLog isolation checks.
# Add this comment to a file that legitimately needs direct ActionLog access
# (e.g. debug endpoints, introspection controllers, testing utilities):
#   // CLAD: ActionLog waiver — <reason>
_ACTION_LOG_WAIVER = re.compile(r'CLAD:\s*ActionLog\s+waiver\s*[—-]', re.IGNORECASE)


def strip_comments_and_strings(source):
    """Strip Java comments, text blocks, and string literals."""
    # Multi-line comments
    s = re.sub(r'/\*.*?\*/', ' ', source, flags=re.DOTALL)
    # Line comments (but not URLs)
    s = re.sub(r'(?<!:)//.*$', ' ', s, flags=re.MULTILINE)
    # Text blocks (SPARQL queries)
    s = re.sub(r'"""[\s\S]*?"""', ' ', s, flags=re.MULTILINE)
    # String literals
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    return s


def read_clad_property(key, default=""):
    """Read a property from clad.properties."""
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
                        if "  #" in val:
                            val = val.split("  #")[0].rstrip()
                        return val
            return default
        parent = d.parent
        if parent == d:
            return default
        d = parent


def find_java_files(root_dir):
    """Yield (relative_path, absolute_path) for Java/Kotlin files."""
    root = Path(root_dir).resolve()
    if not root.is_dir():
        return
    for ext in ("*.java", "*.kt"):
        for p in sorted(root.rglob(ext)):
            if p.is_file():
                yield str(p.relative_to(root)), str(p)


def check_file(filepath):
    """Check a single source file for ActionLog isolation violations.
    Returns list of (line_number, message) defects."""
    defects = []

    try:
        with open(filepath) as fh:
            source = fh.read()
    except (OSError, UnicodeDecodeError):
        return defects

    # Waiver: file contains an explicit ActionLog waiver comment
    if _ACTION_LOG_WAIVER.search(source):
        return defects

    code = strip_comments_and_strings(source)

    # --- Check 1: Direct ActionLog access ---
    matches = _ACTION_LOG_DIRECT_ACCESS.finditer(code)
    for m in matches:
        # Find line number in original source
        lineno = source[:m.start()].count('\n') + 1
        call = m.group(0)
        defects.append((
            lineno,
            f"direct ActionLog access ({call}...) — infrastructure must use "
            f"flowManager.rootAction() + syncDispatcher.awaitResponse(), "
            f"not raw ActionLog queries. Move business logic to a concept "
            f"(R4)",
        ))

    # --- Check 2: Concept graph literals in non-concept code ---
    # Only flag in infrastructure/ files (concepts legitimately reference
    # their own graph names)
    if "/infrastructure/" in filepath:
        graph_matches = _CONCEPT_GRAPH_LITERAL.finditer(code)
        for m in graph_matches:
            literal = m.group(0)[:60]
            # Allow Web concept's own references (request/respond are legit)
            if 'request' in literal or 'respond' in literal:
                continue
            lineno = source[:m.start()].count('\n') + 1
            defects.append((
                lineno,
                f"concept graph or action name in infrastructure code "
                f"({literal}...) — controllers must not know concept "
                f"internals. Use flowManager.rootAction() instead (R4)",
            ))

    # --- Check 3: flowManager/syncDispatcher misuse ---
    engine_matches = _ENGINE_BYPASS_PATTERNS.finditer(code)
    for m in engine_matches:
        lineno = source[:m.start()].count('\n') + 1
        call = m.group(0)[:60]
        defects.append((
            lineno,
            f"unexpected engine method call ({call}...) — infrastructure "
            f"should only call flowManager.rootAction() and "
            f"syncDispatcher.awaitResponse()",
        ))

    return defects


def main():
    parser = argparse.ArgumentParser(
        description="Verify ActionLog access is isolated to concepts and engine")
    parser.add_argument(
        "--app-source-root", default=None,
        help="Root directory containing infrastructure/, concepts/, engine/ "
             "source packages (e.g. app/backend/src/main/java/com/example/app)")
    args = parser.parse_args()

    # Determine app source root
    app_root = args.app_source_root
    if not app_root:
        # Try to derive from clad.properties concept.impl.dir
        concept_dir = read_clad_property("concept.impl.dir", "")
        if concept_dir:
            # concept.impl.dir is e.g. "reference-impl/.../concepts"
            # app root is the parent of the concepts/ directory
            app_root = str(Path(concept_dir).parent)
        else:
            print("FAIL  could not determine app source root. "
                  "Set concept.impl.dir in clad.properties or pass "
                  "--app-source-root.")
            sys.exit(1)

    app_root = os.path.abspath(app_root)
    if not os.path.isdir(app_root):
        print(f"FAIL  app source root not found: {app_root}")
        sys.exit(1)

    # Find the infrastructure directory
    infra_dir = None
    for name in ("infrastructure", "web", "http", "controller", "controllers"):
        candidate = os.path.join(app_root, name)
        if os.path.isdir(candidate):
            infra_dir = candidate
            break

    if not infra_dir:
        print(f"INFO  no infrastructure/ directory found under {app_root} "
              f"— nothing to check")
        sys.exit(0)

    all_defects = []
    files_checked = 0

    # Scan infrastructure files
    for rel_path, abs_path in find_java_files(infra_dir):
        files_checked += 1
        defects = check_file(abs_path)
        if defects:
            print(f"\n  {rel_path}")
            for lineno, msg in defects:
                print(f"    line {lineno}: {msg}")
            all_defects.extend(defects)

    if not files_checked:
        print(f"INFO  no source files found in {infra_dir} — nothing to check")
        sys.exit(0)

    if all_defects:
        print()
        print(f"FAIL  {len(all_defects)} ActionLog isolation violation(s) "
              f"in infrastructure/")
        print()
        print("  Infrastructure (controllers, HTTP handlers) must be "
              "transport-only:")
        print("    1. Normalize input")
        print("    2. Call flowManager.rootAction() to start the flow")
        print("    3. Call syncDispatcher.awaitResponse() to get the result")
        print("    4. Translate output to HTTP")
        print()
        print("  Direct ActionLog access, raw SPARQL queries, and business "
              "logic in")
        print("  controllers violate R4 and break the WYSIWID traceability "
              "chain.")
        print("  Move business logic into concept classes; use syncs for "
              "coordination.")
        sys.exit(1)
    else:
        print(f"PASS  all {files_checked} infrastructure file(s) are "
              f"transport-only — no direct ActionLog access")
        sys.exit(0)


if __name__ == "__main__":
    main()
