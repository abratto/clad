#!/usr/bin/env python3
"""
verify_concept_criteria.py — criteria gate: the mechanical subset of the
concept criteria.

Why this exists:
  A concept is a unit of functionality chunked around one purpose, with an
  operational principle, polymorphic state over a set of individuals, and no
  dependence on other concepts. Most of that is judgment (see the human
  checklist in Stage 02's contract). This script makes the CHECKABLE subset
  deterministic so the judgment checklist is not asked to catch mechanical
  defects (maintenance change `system-scope-concept-vocabulary`, decision D6).

Checks per `<Name>.concept.md`:

  FAIL  operational principle present — a `## Operational principle` section
        whose fenced block is non-empty (the end-to-end witness trace).
  FAIL  no external types — no state or action type is the name of ANOTHER
        concept in the corpus. That is the R1 leak (a concept reaching into a
        neighbour instead of using an opaque id or a type parameter).
  WARN  type parameters declared — the header `concept Name [Params]` should
        declare at least one type parameter (D2).
  WARN  capability naming — the name should denote an ability, not an entity
        noun (advisory; the template's anti-pattern names are `User`, `Post`,
        ...). Jackson's own `Session` is therefore NOT flagged. Machinery
        suffixes (`Service`, `Manager`, `Handler`, ...) are likewise flagged.
  WARN  shape lints (`concept-shape-lint`) — purpose longer than
        `concept.purpose.max-words` (default 12); more state fields than
        `concept.state.max-fields` (default 8) or actions than
        `concept.actions.max-count` (default 10); an operational principle
        citing at most one of the concept's actions (the degenerate
        "state updates so" trace).

Usage:
  python3 verify_concept_criteria.py [--concept-dir features/_system/concepts]
                                     [--advisory]

  Stage 02 passes the feature's proposals plus the canonical corpus, so a
  proposal shadows the corpus spec of the same name:
  python3 verify_concept_criteria.py \
    --concept-dir features/UC-XX-<slug>/stages/02_concepts/output \
    --concept-dir features/_system/concepts

Exit: 0 pass/warn/skip, 1 fail.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artifact_parsers as ap  # noqa: E402

OP_SECTION = re.compile(r"^##\s+Operational principle\s*$(.*?)(?=^##\s|\Z)",
                        re.MULTILINE | re.DOTALL)
STATE_SECTION = re.compile(r"^##\s+State\s*$(.*?)(?=^##\s|\Z)",
                           re.MULTILINE | re.DOTALL)
ACTIONS_SECTION = re.compile(r"^##\s+Actions\s*$(.*?)(?=^##\s|\Z)",
                             re.MULTILINE | re.DOTALL)
HEADER = re.compile(r"^concept\s+(\w+)\s*(?:\[([^\]]*)\])?", re.MULTILINE)
WITNESS = re.compile(r"^\s*(after|then)\b", re.MULTILINE)
CAPITALISED = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")

# Entity nouns the concept template names as anti-patterns. Advisory only:
# a concept is a capability, not the entity noun its set ranges over.
ANTI_PATTERN_NAMES = {
    "User", "Account", "Profile", "Post", "Article", "Comment",
    "Order", "Item", "Product", "Customer", "Message", "Document",
}

# Machinery suffixes are incidental structure, not purpose (CONCEPTS.md:
# "`UserService` is wrong for a different reason: the `Service` suffix is
# incidental machinery, not a purpose"). Advisory, like ANTI_PATTERN_NAMES.
MACHINERY_SUFFIXES = ("Service", "Manager", "Handler", "Helper", "Util",
                      "Controller")

# Shape-lint defaults (maintenance change `concept-shape-lint`), overridable
# in clad.properties. Warnings only — granularity is human judgment; these
# surface the smells a reviewer should look at, never block a gate.
DEFAULT_PURPOSE_MAX_WORDS = 12
DEFAULT_STATE_MAX_FIELDS = 8
DEFAULT_ACTIONS_MAX_COUNT = 10


def _shape_limits():
    """(purpose max words, state max fields, actions max count) from
    clad.properties at the repo root, falling back to the defaults."""
    props_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              os.pardir, "clad.properties")
    values = {}
    if os.path.isfile(props_path):
        with open(props_path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    values[key.strip()] = value.strip()

    def _int(key, default):
        try:
            parsed = int(values.get(key, ""))
            return parsed if parsed > 0 else default
        except ValueError:
            return default

    return (_int("concept.purpose.max-words", DEFAULT_PURPOSE_MAX_WORDS),
            _int("concept.state.max-fields", DEFAULT_STATE_MAX_FIELDS),
            _int("concept.actions.max-count", DEFAULT_ACTIONS_MAX_COUNT))


def _purpose_word_count(text):
    """Words in the `purpose` stanza (indented lines after the bare keyword)."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().lower() == "purpose":
            words = []
            for nxt in lines[i + 1:]:
                stripped = nxt.strip()
                if (not stripped or stripped.startswith("#")
                        or stripped.startswith("```")):
                    break
                words.extend(stripped.split())
            return len(words)
    return 0


def _state_field_count(text):
    """State relation lines: non-blank, non-fence lines of the State block,
    excluding the stateless `*None.*` marker."""
    section = STATE_SECTION.search(text)
    if not section:
        return 0
    body = re.sub(r"```", "", section.group(1))
    count = 0
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("*None.*"):
            continue
        count += 1
    return count


def _principle_action_coverage(text, action_names):
    """Distinct declared action names cited by the operational principle's
    fenced witness trace."""
    section = OP_SECTION.search(text)
    if not section:
        return 0
    body = "\n".join(re.findall(r"```(.*?)```", section.group(1), re.DOTALL))
    return sum(1 for action in action_names
               if re.search(r"\b%s\b" % re.escape(action), body))


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def check_one(path, others):
    """Return (failures, warnings) for one concept file."""
    name = os.path.basename(path).replace(".concept.md", "")
    text = read(path)
    failures, warnings = [], []

    header = HEADER.search(text)
    type_params = (header.group(2).strip() if header and header.group(2) else "")

    # 1. Operational principle present and non-empty.
    op = OP_SECTION.search(text)
    body = op.group(1) if op else ""
    fenced = re.findall(r"```(.*?)```", body, re.DOTALL)
    if not op or not any(WITNESS.search(block) for block in fenced):
        failures.append(
            "no `## Operational principle` witness trace (a non-empty fenced "
            "`after`/`then` block) — the end-to-end test of the concept")

    # 2. No external types: a state/action type named after another concept.
    leak_section = ""
    for section in (STATE_SECTION.search(text), ACTIONS_SECTION.search(text)):
        if section:
            leak_section += section.group(1)
    used_types = set(CAPITALISED.findall(leak_section))
    leaked = sorted(used_types & (others - {name}))
    if leaked:
        failures.append(
            "external type reference(s) %s — a concept must not name another "
            "concept's type (R1); use an opaque id or a type parameter"
            % ", ".join(leaked))

    # 3. Type parameters declared (advisory).
    if not type_params:
        warnings.append(
            "no type parameters declared in the header (`concept %s [ ... ]`)" % name)

    # 4. Capability naming heuristic (advisory).
    if name in ANTI_PATTERN_NAMES:
        warnings.append(
            "`%s` is an entity noun; name the capability instead (advisory)" % name)
    if name.endswith(MACHINERY_SUFFIXES):
        warnings.append(
            "`%s` ends in a machinery suffix — that is incidental structure, "
            "not a purpose; name the capability (advisory)" % name)

    # 5. Shape lints (advisory; maintenance change `concept-shape-lint`).
    purpose_max, state_max, actions_max = _shape_limits()

    words = _purpose_word_count(text)
    if words > purpose_max:
        warnings.append(
            "purpose is %d words (limit %d) — a concept's purpose must be "
            "nameable in a short verb phrase; a long purpose suggests two "
            "capabilities" % (words, purpose_max))

    state_fields = _state_field_count(text)
    if state_fields > state_max:
        warnings.append(
            "%d state fields (limit %d) — a concept this wide is probably "
            "two capabilities sharing a noun" % (state_fields, state_max))

    action_names = [a.name for a in ap.parse_concept(path).actions]
    if len(action_names) > actions_max:
        warnings.append(
            "%d actions (limit %d) — a surface this broad is probably two "
            "concepts" % (len(action_names), actions_max))

    # The end-to-end criterion: a principle citing at most one action has
    # degenerated to "when this action happens, the state updates so".
    if OP_SECTION.search(text) and action_names:
        cited = _principle_action_coverage(text, action_names)
        if cited <= 1:
            warnings.append(
                "operational principle cites %d action(s) — it degenerates "
                "to a state-update narration; the end-to-end criterion "
                "wants a witness trace across the concept's behaviour "
                "(advisory)" % cited)

    return failures, warnings


def main():
    parser = argparse.ArgumentParser(
        description="Verify the mechanical subset of the concept criteria")
    parser.add_argument("--concept-dir", action="append", default=None,
                        help="Concept-spec dir; repeatable. Earlier dirs shadow "
                             "later ones by concept name. Defaults to the "
                             "system corpus.")
    parser.add_argument("--advisory", action="store_true",
                        help="Report failures as warnings (exit 0)")
    args = parser.parse_args()

    dirs = args.concept_dir or ["features/_system/concepts"]
    specs = ap.concept_spec_paths(dirs)
    if not specs:
        print("SKIP  no concept specs under %s" % ", ".join(dirs))
        return 0

    names = set(specs)
    all_failures, all_warnings = [], []
    for name, path in sorted(specs.items()):
        failures, warnings = check_one(path, names)
        all_failures.extend("%s: %s" % (name, f) for f in failures)
        all_warnings.extend("%s: %s" % (name, w) for w in warnings)

    for warning in all_warnings:
        print("WARN  %s" % warning)

    if all_failures:
        label = "WARN" if args.advisory else "FAIL"
        print("%s  %d concept criteria failure(s):" % (label, len(all_failures)))
        for failure in all_failures:
            print("  - %s" % failure)
        return 0 if args.advisory else 1

    print("PASS  %d concept(s) satisfy the mechanical criteria (%d warning(s))"
          % (len(specs), len(all_warnings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
