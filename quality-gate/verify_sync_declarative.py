#!/usr/bin/env python3
"""
verify_sync_declarative.py — Gate: sync implementations must be declarative.

Why this exists:
    CLAD architecture rule R3 requires syncs to be declarative — they express
    coordination in SPARQL patterns, not in imperative Java branching. A sync
    class with if/else/switch statements, for/while loops, or named as a
    Coordinator/Orchestrator violates the WYSIWID contract and turns syncs from
    reviewable declarative rules into imperative procedural code.

    R3 from methodology/implementation/RULES.md:
    "Syncs are declarative, not imperative. A sync says 'when X completes ->
    then Y'. It does not contain branching business logic; that belongs in a
    concept's actions."

    This script catches three specific defects that break the declarative
    contract:

    1. **Coordinator/Orchestrator class names.** A class named
       *Coordinator or *Orchestrator inside the sync directory indicates
       that coordination logic has leaked out of the SPARQL dispatch engine
       and into imperative Java. CLAD's SyncDispatcher engine handles
       coordination declaratively — no Java coordinator is needed.

    2. **Imperative branching in method bodies.** if/else/switch/for/while
       statements inside a sync class mean the author is doing in Java what
       should be done in SPARQL. Different outcomes from a trigger action
       should be separate sync classes (one per outcome path), not a single
       class with if/else chains. SPARQL FILTER handles multi-outcome
       dispatch declaratively.

    3. **Non-final fields.** Mutable instance state in a sync class is a
       red flag — syncs fire repeatedly from the dispatch loop and must be
       stateless. Only static final constants are acceptable.

    This is a profile-agnostic check. The existing ArchUnit test
    (LegibleArchitectureRulesTest) enforces these rules at build time for the
    Java profile; this script catches violations earlier in the CLAD pipeline
    and works for any profile that stores syncs as source files.

Checks:
    1. No class in the sync impl directory matches *Coordinator or *Orchestrator.
    2. No sync class contains imperative branching keywords (if/else/switch/
       for/while/do) in method bodies, after stripping comments and string
       literals (including SPARQL text blocks).
    3. Every field declaration in a sync class is final.

Usage:
    python3 verify_sync_declarative.py --sync-impl-dir <path>
    python3 verify_sync_declarative.py  # reads sync.impl.dir from clad.properties
"""

import argparse
import os
import re
import sys
from pathlib import Path


# Regexes to strip Java annotations and comments
# Matches multi-line /* ... */ comments
_BLOCK_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)
# Matches // line comments (but not http:// or https://)
_LINE_COMMENT_RE = re.compile(r'(?<!:)//.*$', re.MULTILINE)
# Matches Java text blocks ("""...""") — common for SPARQL queries in syncs
_TEXT_BLOCK_RE = re.compile(r'"""[\s\S]*?"""', re.MULTILINE)
# Matches string literals ("..." or '...')
_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')

# Patterns for defects
_COORDINATOR_RE = re.compile(r'\b(?:class|interface|record)\s+(\w*Coordinator\w*)\b')
_ORCHESTRATOR_RE = re.compile(r'\b(?:class|interface|record)\s+(\w*Orchestrator\w*)\b')
_BRANCHING_RE = re.compile(
    r'\b(if|else|switch|for|while)\b'   # standard branching keywords
    r'|do\s*\{',                         # do-while loop (not doSomething)
)
# Matches class/interface/record names from file declarations
_CLASS_DECL_RE = re.compile(r'\b(?:class|interface|record)\s+(\w+)')
# Matches method declarations to track method body entry/exit
_METHOD_DECL_RE = re.compile(
    r'^\s*(?:public|protected|private|static|\s)*'
    r'(?:[<>\[\]\w\s,]+)\s+'          # return type
    r'(\w+)\s*'                        # method name
    r'\([^)]*\)\s*'                    # parameter list
    r'(?:throws\s+\S+(?:\s*,\s*\S+)*)?\s*'  # throws clause
    r'\{',
    re.MULTILINE,
)
# Matches field declarations that aren't final
_FIELD_RE = re.compile(
    r'^\s*'                            # leading whitespace
    r'(?!(?:\s*//|\s*/\*|@|final))'    # not a comment, annotation, or final
    r'(?:public|protected|private|static|\s)+'
    r'(?:[<>\[\]\w\s,]+)\s+'           # type
    r'(\w+)\s*'                        # field name
    r'(?:=|;)'                         # assignment or declaration
    r'(?![^;]*\bfinal\b)',             # not followed by 'final' later
    re.MULTILINE,
)


def read_clad_property(key, default=""):
    """Read a property from clad.properties by walking up from cwd."""
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


def strip_comments_and_strings(source):
    """Remove comments, text blocks, and string literals from Java source.
    Returns a version of the source where only code structure remains,
    suitable for branch-detection regex matching."""
    s = source
    s = _BLOCK_COMMENT_RE.sub(' ', s)
    s = _LINE_COMMENT_RE.sub(' ', s)
    s = _TEXT_BLOCK_RE.sub(' ', s)
    s = _STRING_RE.sub('""', s)
    return s


def extract_method_bodies(source):
    """Extract method body content for each method in the source.
    Uses brace-counting to handle nested blocks. Returns list of
    (method_name, body_source) tuples."""
    stripped = strip_comments_and_strings(source)
    bodies = []

    for m in _METHOD_DECL_RE.finditer(stripped):
        name = m.group(1)
        start = m.start()
        # Find the opening brace
        brace_pos = stripped.index('{', m.end() - 1)
        # Count braces to find matching close
        depth = 0
        pos = brace_pos
        while pos < len(stripped):
            if stripped[pos] == '{':
                depth += 1
            elif stripped[pos] == '}':
                depth -= 1
                if depth == 0:
                    body = source[brace_pos:pos + 1]
                    bodies.append((name, body))
                    break
            pos += 1

    return bodies


def check_file(filepath):
    """Check a single Java source file for declarative violations.
    Returns a list of (line_number, message) defect tuples."""
    defects = []

    try:
        with open(filepath) as fh:
            source = fh.read()
    except (OSError, UnicodeDecodeError):
        return defects

    filename = os.path.basename(filepath)

    # --- Check 1: Coordinator / Orchestrator class names ---
    coord_matches = _COORDINATOR_RE.findall(source)
    for name in coord_matches:
        defects.append((0, f"coordinator class '{name}' — coordination "
                           f"belongs in the SyncDispatcher engine, not in a "
                           f"coordinator class (R3)"))

    orch_matches = _ORCHESTRATOR_RE.findall(source)
    for name in orch_matches:
        defects.append((0, f"orchestrator class '{name}' — orchestration "
                           f"belongs in SPARQL patterns, not in a Java "
                           f"orchestrator (R3)"))

    # --- Check 2: Imperative branching in method bodies ---
    bodies = extract_method_bodies(source)
    for method_name, body in bodies:
        # Skip trivial methods (constructors often call super(), that's fine)
        if method_name in ("syncName",) and len(body) < 200:
            continue
        # Strip to code-only for branch detection
        code = strip_comments_and_strings(body)
        branches = _BRANCHING_RE.findall(code)
        if branches:
            unique = sorted(set(branches))
            defects.append((0, f"imperative branching in method "
                               f"'{method_name}()' — contains {unique}. "
                               f"Use separate sync classes per outcome path "
                               f"and SPARQL FILTER for multi-outcome dispatch "
                               f"(R3)"))

    # --- Check 3: Non-final fields ---
    code = strip_comments_and_strings(source)
    # Remove method bodies to avoid matching local variables
    bodies_marker = extract_method_bodies(source)
    body_ranges = []
    pos = 0
    for _name, body in bodies_marker:
        # Re-find the body in the original source
        # This is approximate — use the stripped code
        pass

    # Simple approach: scan for non-final field declarations at class level
    # by finding lines with field-like patterns outside methods
    lines = source.splitlines()
    in_method = False
    brace_depth = 0

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("//"):
            continue
        if line_stripped.startswith("/*"):
            continue

        # Track brace depth for class body (simplified: count { and })
        brace_depth += line_stripped.count('{') - line_stripped.count('}')

        # When we enter a method (after a method declaration), skip field checks
        # Method check: line matches a method signature (has (params) and {)
        if re.match(r'.*\(.*\)\s*(?:throws\s+\S+)?\s*\{', line_stripped):
            in_method = True
            continue

        # When brace_depth drops below class level, reset
        if brace_depth <= 0:
            in_method = False

        if in_method:
            continue

        # Detect non-final fields
        # Match: access modifier + type + name
        m = re.match(
            r'^\s*(?:public|protected|private)\s+(?!final\b)'
            r'(?:static\s+)?'
            r'(?!.*\bfinal\b)'
            r'(\w+(?:<[^>]+>)?(?:\s*\[\])?)\s+'
            r'(\w+)\s*[=;]',
            line,
        )
        if m:
            type_name = m.group(1)
            field_name = m.group(2)
            # Skip if it's actually a method (has parens)
            if '(' not in line_stripped and ')' not in line_stripped:
                # Make sure it's not a local variable (inside a static block, etc.)
                if brace_depth <= 1:
                    defects.append((
                        i + 1,
                        f"non-final field '{field_name}' ({type_name}) — "
                        f"syncs must be stateless; declare as final if it is "
                        f"a constant (R3)",
                    ))

    return defects


def main():
    parser = argparse.ArgumentParser(
        description="Verify sync implementations are declarative (R3)")
    parser.add_argument(
        "--sync-impl-dir", default=None,
        help="Path to sync implementation source directory. "
             "If not given, reads sync.impl.dir from clad.properties.")
    args = parser.parse_args()

    sync_dir = args.sync_impl_dir or read_clad_property("sync.impl.dir")
    if not sync_dir:
        print("FAIL  sync.impl.dir not found in clad.properties and "
              "--sync-impl-dir not given.")
        sys.exit(1)

    sync_dir = os.path.abspath(sync_dir)
    if not os.path.isdir(sync_dir):
        print(f"FAIL  sync implementation directory not found: {sync_dir}")
        sys.exit(1)

    all_defects = []
    java_files = sorted(
        p for p in Path(sync_dir).rglob("*.java")
        if p.is_file()
    )

    if not java_files:
        print(f"INFO  no Java files found in {sync_dir} — nothing to check")
        sys.exit(0)

    for filepath in java_files:
        defects = check_file(str(filepath))
        if defects:
            rel = os.path.relpath(filepath, start=os.getcwd())
            print(f"\n  {rel}")
            for lineno, msg in defects:
                loc = f"  line {lineno}: " if lineno else "  "
                print(f"    {loc}{msg}")
            all_defects.extend(defects)

    if all_defects:
        print()
        print(f"FAIL  {len(all_defects)} declarative violation(s) in "
              f"{len(set(str(f) for f in java_files if check_file(str(f))))} "
              f"file(s)")
        print()
        print("  CLAD syncs must be declarative (R3). Coordination is expressed")
        print("  in SPARQL patterns, not in Java branching. Split outcome paths")
        print("  into separate sync classes; use SPARQL FILTER for dispatch.")
        print("  See methodology/architecture/SYNCHRONIZATIONS.md.")
        sys.exit(1)
    else:
        print(f"PASS  all sync classes in {sync_dir} are declarative")
        sys.exit(0)


if __name__ == "__main__":
    main()
