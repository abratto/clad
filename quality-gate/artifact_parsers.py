#!/usr/bin/env python3
"""
artifact_parsers.py — shared parsers for CLAD markdown artefacts.

Single source of truth for reading the canonical artefact formats:

  - chain tables       (01b)  -> list of ChainRow
  - responsibility map (01a)  -> dict concept -> ResponsibilityMapEntry
  - concept specs      (02)   -> dict concept -> ConceptSpec
  - sync specs         (03)   -> list of SyncSpec
  - dependency cards   (03a)  -> dict concept -> set of actions
  - SPECs              (04b)  -> dict (concept, action) -> outcomes
  - use case           (01)   -> set of scenario names
  - goals              (00)   -> set of in-scope goal phrases

Both the `verify_*.py` scripts (checks) and the `generate_*.py` scripts
(producers) import from here, so a grammar change is made in one place and
the checker and generator cannot drift apart.

These functions are extracted verbatim from the existing verify scripts —
their behaviour must not change. The one addition is richer return types
(dataclasses) so generators get the structured data they need, not just the
cross-reference sets the verifiers needed.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# --------------------------------------------------------------------------
# Chain tables (Stage 01b)
# --------------------------------------------------------------------------

# U+2227 LOGICAL AND — the join separator in a composite chain-table `When`
# cell (see maintenance/engine-declarative-join-collect.md).
AND = "\u2227"


@dataclass
class Conjunct:
    """One `when` conjunct.

    Chain tables spell a conjunct `[name: ]Concept/action[Outcome]` and sync
    specs spell it `[name: ]Concept/action: [ inputs ] => [ Outcome ; fields ]`.
    `name` is None for the classic single, unnamed trigger. `outcome` is the
    raw completion token, including any parenthesised payload
    (`Found(userId)`, `ok`, `Released(blankFields)`).
    """
    name: Optional[str]
    concept: str
    action: str
    outcome: str
    inputs: str = ""


@dataclass
class ChainRow:
    """One row of a chain-table (the `# | When | Then | Inputs | Outcome | Why`
    shape). Column 0 is the row number; concept/action are normalised to
    slash notation. `outcome_base` is the outcome with parenthesised payload
    removed (`Found(userId)` -> `Found`), and `outcome_payload` is the raw
    parenthesised content (or None). `then_suffix` is the bracketed action
    suffix when present (`[200]`, `[401]`) — these mark terminal respond rows.

    `conjuncts` is the ordered list of `When` conjuncts. A classic row yields
    exactly one unnamed conjunct; a join row yields >=1 `∧`-separated
    conjuncts (each optionally named). `composite_when` is True only when the
    raw cell used the `∧` separator.
    """
    row_num: int
    when: str
    then_concept: str
    then_action: str
    then_suffix: Optional[str]
    inputs: str
    outcome_raw: str
    outcome_base: str
    outcome_payload: Optional[str]
    why: str
    outcome_tokens: List[str] = field(default_factory=list)
    outcome_bases: List[str] = field(default_factory=list)
    then_raw: str = ""
    conjuncts: List[Conjunct] = field(default_factory=list)
    composite_when: bool = False


_CHAIN_CONJUNCT_RE = re.compile(
    r"(?:([A-Za-z_]\w*)\s*:\s*)?"          # optional conjunct name
    r"([A-Za-z_]\w*)\s*[./]\s*([A-Za-z_]\w*)"  # Concept.action / Concept/action
    r"\s*(?:\[([^\]]*)\])?\s*$"            # optional [Outcome]
)


def parse_chain_when(cell: str) -> Tuple[List[Conjunct], bool]:
    """Parse a chain-table `When` cell into ordered conjuncts.

    Returns `(conjuncts, composite)`. A classic cell yields exactly one
    unnamed conjunct; a join cell (>=1 `∧`-separated conjuncts, each
    optionally named `name: Concept/action[Outcome]`) yields one Conjunct per
    part. `composite` is True when the raw cell used the `∧` separator.
    """
    raw = cell.replace("`", "").strip()
    composite = AND in raw
    parts = raw.split(AND) if composite else [raw]
    conjuncts: List[Conjunct] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = _CHAIN_CONJUNCT_RE.match(part)
        if not m:
            continue
        conjuncts.append(Conjunct(
            name=m.group(1),
            concept=m.group(2),
            action=m.group(3),
            outcome=(m.group(4) or "").strip(),
        ))
    return conjuncts, composite


def _split_row(line: str) -> List[str]:
    """Split a Markdown row without treating pipes in code spans as columns."""
    cells: List[str] = []
    current: List[str] = []
    in_code = False
    for char in line:
        if char == "`":
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def parse_chain_table(path: str) -> List[ChainRow]:
    """Parse one chain-table file into ordered ChainRows."""
    rows: List[ChainRow] = []
    with open(path) as f:
        content = f.read()
    lines = content.split("\n")
    in_table = False
    for line in lines:
        if re.match(r"^\|[-:\s]+\|[-:\s]+", line):
            in_table = True
            continue
        if not in_table:
            continue
        if line.strip() == "" or not line.startswith("|"):
            in_table = False
            continue
        cols = _split_row(line)
        if not (cols and cols[1].isdigit()):
            continue
        num = int(cols[1])
        when_col = cols[2]
        then_col = cols[3]
        inputs_col = cols[4] if len(cols) > 4 else ""
        outcome_col = cols[5] if len(cols) > 5 else ""
        why_col = cols[6] if len(cols) > 6 else ""

        # Match `Concept.action` (action may carry a suffix like [200],
        # so do not require a closing backtick). Mirrors the existing
        # verify_action_chain.py regex so terminal `Web.respond[200]`
        # rows are not dropped. The suffix (`[200]`) is captured separately.
        m = re.search(r"`([A-Za-z]+)\.([A-Za-z]+)(\[[^\]]*\])?", then_col)
        if not m:
            continue
        concept, action = m.group(1), m.group(2)
        then_suffix = m.group(3) if m.group(3) else None

        # Each row is one branch, so the Outcome cell must contain one token.
        # Keep all tokens in the parsed representation so malformed legacy
        # union cells cannot be silently truncated by downstream consumers.
        outcome_tokens = re.findall(r"`([^`]+)`", outcome_col)
        outcome_raw = outcome_tokens[0] if outcome_tokens else ""
        outcome_bases = [re.sub(r"\(.*?\)", "", token).strip()
                 for token in outcome_tokens]
        outcome_base = outcome_bases[0] if outcome_bases else ""
        payload_match = re.search(r"\(([^)]*)\)", outcome_raw)
        outcome_payload = payload_match.group(1) if payload_match else None

        conjuncts, composite_when = parse_chain_when(when_col)

        rows.append(ChainRow(
            row_num=num,
            when=when_col.strip("`"),
            then_concept=concept,
            then_action=action,
            then_suffix=then_suffix,
            inputs=inputs_col.strip("`"),
            outcome_raw=outcome_raw,
            outcome_base=outcome_base,
            outcome_payload=outcome_payload,
            why=why_col,
            outcome_tokens=outcome_tokens,
            outcome_bases=outcome_bases,
            then_raw=then_col,
            conjuncts=conjuncts,
            composite_when=composite_when,
        ))
    return rows


def parse_chain_table_actions(chain_dir: str) -> Set[str]:
    """Set of Concept/action from the CANONICAL per-scenario chain tables.

    The consolidated `*-all-scenarios-chain.md` file is a derived,
    non-canonical view with a different column layout (an extra `Scenario(s)`
    column); it is excluded here so only the authoritative per-scenario rows
    contribute. This matches the existing verify_action_chain.py behaviour.
    """
    actions: Set[str] = set()
    if not os.path.isdir(chain_dir):
        return actions
    for fname in sorted(os.listdir(chain_dir)):
        if not fname.endswith("-chain.md") or fname.endswith("-all-scenarios-chain.md"):
            continue
        for row in parse_chain_table(os.path.join(chain_dir, fname)):
            actions.add(f"{row.then_concept}/{row.then_action}")
    return actions


# --------------------------------------------------------------------------
# Responsibility map (Stage 01a)
# --------------------------------------------------------------------------

@dataclass
class ResponsibilityMapEntry:
    concept: str
    owned_state: str
    owned_actions: List[str]
    notes: str


def parse_responsibility_map(path: str) -> Dict[str, ResponsibilityMapEntry]:
    entries: Dict[str, ResponsibilityMapEntry] = {}
    with open(path) as f:
        in_table = False
        for line in f:
            if line.strip().startswith("| Concept | Owned state"):
                in_table = True
                continue
            if in_table:
                if re.match(r"^\|[\s\-:]+\|", line):
                    continue
                if not line.startswith("|"):
                    in_table = False
                    continue
                parts = _split_row(line)
                if len(parts) >= 4:
                    concept = parts[1].strip("`")
                    owned_state = parts[2]
                    owned_actions = re.findall(r"`([^`]+)`", parts[3])
                    notes = parts[4] if len(parts) > 4 else ""
                    entries[concept] = ResponsibilityMapEntry(
                        concept=concept,
                        owned_state=owned_state,
                        owned_actions=owned_actions,
                        notes=notes,
                    )
    return entries


def parse_resp_map_actions(path: str) -> Set[str]:
    """Set of Concept/action from the responsibility map's Owned actions col."""
    actions: Set[str] = set()
    for concept, entry in parse_responsibility_map(path).items():
        for a in entry.owned_actions:
            actions.add(f"{concept}/{a}")
    return actions


# --------------------------------------------------------------------------
# Concept specs (Stage 02)
# --------------------------------------------------------------------------

@dataclass
class ActionSignature:
    name: str
    raw_line: str


@dataclass
class ConceptSpec:
    name: str
    purpose: str
    state_lines: List[str]
    actions: List[ActionSignature]
    operational_principle: str = ""


def parse_concept(path: str) -> ConceptSpec:
    """Parse one *.concept.md file. Actions are top-level `name [ args ]` lines.

    State is the relational block inside the ``` fence following `## State`.
    """
    concept = os.path.basename(path).replace(".concept.md", "")
    actions: List[ActionSignature] = []
    state_lines: List[str] = []
    in_state = False
    fence_depth = 0
    with open(path) as f:
        text = f.read()
    for line in text.split("\n"):
        stripped = line.strip()
        if in_state:
            if stripped.startswith("```"):
                fence_depth += 1
                if fence_depth >= 2:
                    in_state = False  # second fence closes the block
                continue
            if fence_depth >= 1 and stripped:
                state_lines.append(stripped)
            continue
        if stripped.startswith("## State"):
            in_state = True
            fence_depth = 0
            continue
        m = re.match(r"^([a-z][A-Za-z0-9]*)\s+\[", stripped)
        if m:
            actions.append(ActionSignature(name=m.group(1), raw_line=stripped))
    # Dedupe action names while preserving first-seen order (Format B case-split
    # outcomes produce one `action [ ]` line per outcome).
    seen = set()
    deduped: List[ActionSignature] = []
    for a in actions:
        if a.name not in seen:
            seen.add(a.name)
            deduped.append(a)
    return ConceptSpec(name=concept, purpose="",
                       state_lines=state_lines, actions=deduped)


def parse_concept_actions(concept_dir: str) -> Set[str]:
    """Set of Concept/action from concept spec files."""
    actions: Set[str] = set()
    if not os.path.isdir(concept_dir):
        return actions
    for fname in sorted(os.listdir(concept_dir)):
        if not fname.endswith(".concept.md"):
            continue
        concept = fname.replace(".concept.md", "")
        for a in parse_concept(os.path.join(concept_dir, fname)).actions:
            actions.add(f"{concept}/{a.name}")
    return actions


# --------------------------------------------------------------------------
# State-relation parsing (concept `## State` section)
# --------------------------------------------------------------------------

@dataclass
class StateRelation:
    """One relational state fact `field: SubjectType -> FieldType -- multiplicity`.

    `multiplicity` is the raw `--` annotation (e.g. `mandatory`, `optional`,
    `mandatory, unique`, `zero or more`); `unique` is True when the annotation
    contains `unique`."""
    field: str
    subject_type: str
    value_type: str
    multiplicity: str
    unique: bool


def parse_state_relations(state_lines: List[str]) -> List[StateRelation]:
    """Parse `## State` code-block lines into StateRelation facts.

    Matches `field: SubjectType -> FieldType -- mandatory`, `-- optional`,
    `-- zero or more`, and compound annotations (`-- mandatory, unique`).
    Lines that do not match (e.g. prose, blank) are skipped.
    """
    relations: List[StateRelation] = []
    for line in state_lines:
        m = re.match(
            r"^(\w+)\s*:\s*([\w<>,\[\] ]+?)\s*->\s*([\w<>,\[\] ]+?)(?:\s+--\s+(.*))?$",
            line)
        if not m:
            # Also accept a bare map/collection form: `field: Map<K,V>` (no arrow).
            m2 = re.match(r"^(\w+)\s*:\s*([\w<>,\[\] ]+)$", line)
            if m2:
                relations.append(StateRelation(
                    field=m2.group(1), subject_type="", value_type=m2.group(2).strip(),
                    multiplicity="", unique=False))
            continue
        field = m.group(1)
        subject = m.group(2).strip()
        value = m.group(3).strip()
        annotation = (m.group(4) or "").strip()
        unique = "unique" in annotation.lower()
        relations.append(StateRelation(
            field=field, subject_type=subject, value_type=value,
            multiplicity=annotation, unique=unique))
    return relations


# --------------------------------------------------------------------------
# Sync specs (Stage 03)
# --------------------------------------------------------------------------

@dataclass
class SyncSpec:
    name: str
    filename: str
    trigger_concept: str
    trigger_action: str
    trigger_outcome: str
    then_targets: List[Tuple[str, str]]  # (concept, action)
    cited_scenarios: List[str]
    has_pattern_d: bool
    pattern_d_concepts: List[str] = field(default_factory=list)
    route_literals: Tuple[str, ...] = ()  # matched-literal signature (R15)
    conjuncts: List[Conjunct] = field(default_factory=list)
    is_join: bool = False
    collect_forms: List[str] = field(default_factory=list)


def extract_block(text: str, keyword: str) -> str:
    """Return the content of the first `<keyword> { ... }` block, matching
    nested braces. Falls back to a bare `partition('}')` slice when balanced,
    so classic single-block specs parse exactly as before.
    """
    marker = keyword + " {"
    idx = text.find(marker)
    if idx < 0:
        return ""
    start = idx + len(keyword) + 1  # index of the opening '{'
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    return text[start + 1:]


# A sync `when` conjunct: `[name: ]Concept/action: [ inputs ] => [ completion ]`.
# The optional name is only matched when an identifier is followed by `:`
# before another `Concept/action` token, so the classic unnamed trigger still
# parses byte-for-byte.
_SYNC_CONJUNCT_RE = re.compile(
    r"(?:([A-Za-z_]\w*)\s*:\s*)?"
    r"([A-Za-z_]\w*)\s*/\s*([A-Za-z_]\w*)\s*:\s*"
    r"\[([^\]]*)\]\s*=>\s*\[([^\]]*)\]")


def _first_completion_token(right: str) -> str:
    """First token on the right of a `=> [...]` arrow (`ok ; userId: ?u` -> `ok`)."""
    right = (right or "").strip()
    outcome_m = re.match(r"([A-Za-z][A-Za-z0-9_]*)", right)
    return outcome_m.group(1) if outcome_m else right


# Declarative collect `where` forms (maintenance/engine-declarative-join-collect.md).
# Detected for Pattern-D / aggregate reporting; the forms are:
#   collect ( <source> as ?var )
#   collect distinct ( <source> as ?var )
#   collect by ?groupKey ( <source> as ?var )
_COLLECT_RE = re.compile(
    r"\bcollect\b\s*(distinct\b\s*)?(?:by\s+\?\w+\s*)?\([^)]*\)")


def parse_sync(path: str) -> Optional[SyncSpec]:
    """Parse one *.sync.md file into its name, trigger(s), targets, and flags."""
    if not os.path.isfile(path) or not path.endswith(".sync.md"):
        return None
    fname = os.path.basename(path)
    with open(path) as f:
        text = f.read()

    name_match = re.search(r"^sync\s+(\w+)", text, re.MULTILINE)
    name = name_match.group(1) if name_match else fname.replace(".sync.md", "")

    when_block = extract_block(text, "when")
    then_block = extract_block(text, "then")

    conjuncts: List[Conjunct] = []
    for m in _SYNC_CONJUNCT_RE.finditer(when_block):
        conjuncts.append(Conjunct(
            name=m.group(1),
            concept=m.group(2),
            action=m.group(3),
            inputs=m.group(4).strip(),
            outcome=_first_completion_token(m.group(5))))
    # A rule is a join when it declares more than one conjunct, or a single
    # *named* conjunct (the agreed multi-`when` syntax).
    is_join = len(conjuncts) > 1 or any(c.name for c in conjuncts)

    if conjuncts:
        primary = conjuncts[0]
        trigger_concept, trigger_action = primary.concept, primary.action
        trigger_outcome = primary.outcome
    else:
        trigger_concept, trigger_action, trigger_outcome = "", "", ""

    then_targets: List[Tuple[str, str]] = []
    for m in re.finditer(r"([A-Za-z]+)/([A-Za-z]+)\s*:", then_block):
        then_targets.append((m.group(1), m.group(2)))


    cited: List[str] = re.findall(r"—\s+scenario\s+[\"`']([^\"`']+)[\"`']", text)

    # Pattern D = a concept-state read in the where block: `Concept: { ... }`
    where_block = extract_block(text, "where")
    has_pattern_d = bool(re.search(r"[A-Za-z]+\s*:\s*\{", where_block))
    pattern_d_concepts = re.findall(r"([A-Za-z][A-Za-z0-9]*)\s*:\s*\{", where_block)
    # DSL-authored concept-state reads and inverse-index reads
    # (stateRead("Concept", ...) / subjects("Concept", ...) / fanOut(?, "Concept", ...)):
    # the where block may use the fluent factories instead of the
    # `Concept: { ... }` prose form; detect both so Pattern-D audits
    # (Stage 03a dependency cards) see the reads.
    for c in re.findall(r"(?:stateRead|subjects)\s*\(\s*\"([A-Za-z][A-Za-z0-9]*)\"", where_block) \
            + re.findall(r"fanOut\s*\(\s*\"[^\"]*\"\s*,\s*\"([A-Za-z][A-Za-z0-9]*)\"", where_block):
        if c not in pattern_d_concepts:
            pattern_d_concepts.append(c)
    has_pattern_d = has_pattern_d or bool(pattern_d_concepts)
    # Declarative collect forms (collect / collect distinct / collect by).
    collect_forms = [m.group(0).strip() for m in _COLLECT_RE.finditer(where_block)]
    # Route literal signature (R15): matched literal constraints the when/where
    # blocks apply to the trigger/targets (e.g. `check = "entry"`,
    # `cause = "stale"`). Value-side literals only; ?var binds excluded.
    route_literals_l: List[str] = []
    for clause in (when_block, where_block):
        for m in re.finditer(r"(\w+)\s*=\s*([\"'])([^\"']*)\2", clause):
            route_literals_l.append(f"{m.group(1)}={m.group(3)}")
        for m in re.finditer(r"(\w+)\s*=\s*([A-Za-z][A-Za-z0-9_]*)\s*[;,}]?\s*$",
                             clause, re.MULTILINE):
            if m.group(1) != "route":
                route_literals_l.append(f"{m.group(1)}={m.group(2)}")
    route_literals = tuple(sorted(set(route_literals_l)))

    return SyncSpec(
        name=name,
        filename=fname,
        trigger_concept=trigger_concept,
        trigger_action=trigger_action,
        trigger_outcome=trigger_outcome,
        then_targets=then_targets,
        cited_scenarios=cited,
        route_literals=route_literals,
        has_pattern_d=has_pattern_d,
        pattern_d_concepts=pattern_d_concepts,
        conjuncts=conjuncts,
        is_join=is_join,
        collect_forms=collect_forms,
    )


def parse_syncs(sync_dir: str) -> List[SyncSpec]:
    """List of SyncSpec for every *.sync.md in a directory."""
    if not os.path.isdir(sync_dir):
        return []
    return [s for fname in sorted(os.listdir(sync_dir))
            if fname.endswith(".sync.md")
            for s in [parse_sync(os.path.join(sync_dir, fname))] if s]


def parse_sync_actions(sync_dir: str) -> Set[str]:
    """Set of Concept/action from sync `then` clauses."""
    actions: Set[str] = set()
    for s in parse_syncs(sync_dir):
        for concept, action in s.then_targets:
            actions.add(f"{concept}/{action}")
    return actions


def parse_sync_cited_scenarios(sync_dir: str) -> Set[str]:
    cited: Set[str] = set()
    for s in parse_syncs(sync_dir):
        cited.update(s.cited_scenarios)
    return cited


# --------------------------------------------------------------------------
# Dependency cards (Stage 03a)
# --------------------------------------------------------------------------

def parse_dep_card_actions(dep_dir: str) -> Set[str]:
    actions: Set[str] = set()
    if not os.path.isdir(dep_dir):
        return actions
    for fname in sorted(os.listdir(dep_dir)):
        if not fname.endswith("-card.md"):
            continue
        concept = fname.replace("-card.md", "")
        with open(os.path.join(dep_dir, fname)) as f:
            for line in f:
                m = re.match(r"^\|\s*`(\w+)`\s*\|", line)
                if m:
                    actions.add(f"{concept}/{m.group(1)}")
    return actions


# --------------------------------------------------------------------------
# SPECs (Stage 04b)
# --------------------------------------------------------------------------

def parse_spec_actions(spec_dir: str) -> Set[str]:
    actions: Set[str] = set()
    if not os.path.isdir(spec_dir):
        return actions
    for fname in sorted(os.listdir(spec_dir)):
        if not fname.endswith(".spec.md"):
            continue
        concept = fname.replace(".spec.md", "")
        with open(os.path.join(spec_dir, fname)) as f:
            for line in f:
                m = re.match(r"^###\s+`(\w+)\(", line.strip())
                if m:
                    actions.add(f"{concept}/{m.group(1)}")
    return actions


def parse_spec_outcomes(spec_dir: str) -> Dict[Tuple[str, str], Set[str]]:
    """{(concept, action): set(outcome strings)} from SPEC files."""
    specs: Dict[Tuple[str, str], Set[str]] = {}
    if not os.path.isdir(spec_dir):
        return specs
    for fname in sorted(os.listdir(spec_dir)):
        if not fname.endswith(".spec.md"):
            continue
        concept = fname.replace(".spec.md", "")
        path = os.path.join(spec_dir, fname)
        with open(path) as f:
            content = f.read()
        action = None
        for line in content.split("\n"):
            m_action = re.match(r"^###\s+`(\w+)\(", line)
            if m_action:
                action = m_action.group(1)
                specs.setdefault((concept, action), set())
                continue
            if action is None:
                continue
            m_out = re.match(r"^- \*\*Outcomes.*?:\*\*\s+(.+)$", line.strip())
            if m_out:
                specs[(concept, action)] = set(re.findall(r"`([^`]+)`", m_out.group(1)))
                action = None
    return specs


# --------------------------------------------------------------------------
# Use case (Stage 01) and goals (Stage 00)
# --------------------------------------------------------------------------

def parse_derivation_map(path: str) -> List[Tuple[str, str, str, str, str]]:
    """Parse a Stage 04d/04e derivation map.

    Returns a list of `(test_class, test_method, outcome, concept, action)`,
    accepting both the template Format A
    (`### Concept.action -> test class: Class` + `| # | @Nested | Test method |
    Outcome | ... |`) and its legacy no-`@Nested` header, plus Format B
    (`## Concept.action(...) -> Result`). Single source of truth for the
    grammar shared by `verify_concept_test_derivation` and the generators.
    """
    derivations: List[Tuple[str, str, str, str, str]] = []
    current_concept = None
    current_action = None
    current_test_class = None
    table_format = None
    format_a_has_nested = False
    with open(path) as handle:
        lines = handle.readlines()
    for line in lines:
        if "Test method" in line and "Outcome" in line:
            format_a_has_nested = "@Nested" in line
        m_a = re.match(
            r"^###\s+`(\w+)\.(\w+)`\s*.*?→\s*test\s+class:\s*`(\w+)`",
            line.strip())
        if m_a:
            current_concept, current_action, current_test_class = m_a.groups()
            table_format = 'a'
            continue
        m_b = re.match(r"^##\s+(\w+)\.(\w+)\(.*?\).*?->", line.strip())
        if m_b:
            current_concept, current_action = m_b.groups()
            current_test_class = None
            table_format = 'b'
            continue
        if current_concept is None or current_action is None:
            continue
        if not re.match(r"^\|\s*\d+\s*\|", line.strip()):
            continue
        cols = [c.strip() for c in line.strip().split("|")]
        cols = [c for c in cols if c]
        if table_format == 'a':
            if format_a_has_nested and len(cols) >= 5:
                derivations.append((
                    current_test_class, cols[2].strip("`").rstrip("()"),
                    cols[3].strip("`"), current_concept, current_action))
            elif not format_a_has_nested and len(cols) >= 4:
                derivations.append((
                    current_test_class, cols[1].strip("`").rstrip("()"),
                    cols[2].strip("`"), current_concept, current_action))
        elif table_format == 'b' and len(cols) >= 4:
            derivations.append((
                cols[2].strip("`"), cols[3].strip("`").rstrip("()"),
                cols[1].strip("`"), current_concept, current_action))
    return derivations


def parse_feature_scenarios(path: str):
    """Return `(scenarios, in_outline)` for a Gherkin `.feature` file.

    `scenarios` maps Scenario/Scenario Outline name -> its raw lines.
    `in_outline` is the last-seen scenario's outline flag (kept for the
    existing `verify_gherkin_derivation` behavior).
    """
    scenarios = {}
    current_name = None
    current_lines = []
    in_outline = False
    with open(path) as handle:
        lines = handle.readlines()
    for line in lines:
        m_scenario = re.match(
            r"^\s*(?:Scenario|Scenario\s+Outline):\s+(.+)$", line.strip())
        if m_scenario:
            if current_name:
                scenarios[current_name] = current_lines
            current_name = m_scenario.group(1).strip()
            current_lines = [line]
            in_outline = "Outline" in line
        elif current_name:
            current_lines.append(line)
    if current_name:
        scenarios[current_name] = current_lines
    return scenarios, in_outline


def parse_scenario_names(usecase_path: str) -> Set[str]:
    names: Set[str] = set()
    with open(usecase_path) as f:
        for line in f:
            m = re.match(r"^### Scenario:\s+(.+)$", line.strip())
            if m:
                names.add(m.group(1).strip())
    return names


def parse_goals(path: str) -> Set[str]:
    """Return the in-scope goal names from `goals.md`.

    Reads the `| Actor | Goal | ... | In scope? |` table header, then keeps
    only rows whose `In scope?` column starts with `yes`. Rows without an
    `In scope?` column are kept (older goal tables). Out-of-scope goals must
    not be counted as coverage targets.
    """
    goals: Set[str] = set()
    header: List[str] = []
    in_table = False
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        if line.strip().startswith("| Actor | Goal |"):
            header = [c.strip().lower() for c in _split_row(line)]
            in_table = True
            continue
        if in_table:
            if line.strip() == "" or line.startswith("##"):
                in_table = False
                continue
            if re.match(r"^\|[\s\-:]+\|", line):
                continue
            parts = _split_row(line)
            if len(parts) < 3:
                continue
            try:
                goal_idx = header.index("goal")
            except ValueError:
                goal_idx = 2
            try:
                scope_idx = header.index("in scope?")
            except ValueError:
                scope_idx = None
            if scope_idx is not None and scope_idx < len(parts):
                if not parts[scope_idx].strip().lower().startswith("yes"):
                    continue
            goal = parts[goal_idx].strip().strip("`").strip()
            if goal:
                goals.add(goal)
    return goals


# --------------------------------------------------------------------------
# Naming helpers shared by checks and generators
# --------------------------------------------------------------------------

def slugify(name: str) -> str:
    s = name.strip()
    # Split camelCase / acronym runs so a goal like `CheckLiveness` slugs to
    # `check-liveness` and matches a kebab-case scenario of the same name.
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def feature_slug(feature_root: str) -> str:
    """Derive the use-case feature slug from its H1 (`# UC-XX — Ping` -> `ping`)."""
    usecase = os.path.join(feature_root, "stages", "01_usecase", "output",
                           "usecase.md")
    if os.path.isfile(usecase):
        with open(usecase, encoding="utf-8") as handle:
            text = handle.read()
        m = re.search(r"^#\s+(?:UC-[\w-]+\s*[—–-]\s*)?(.+)$", text, re.MULTILINE)
        if m:
            slug = slugify(m.group(1))
            if slug:
                return slug
    return slugify(os.path.basename(feature_root.rstrip("/")).replace("UC-", "", 1))


def expected_stage_outputs(feature_root: str) -> Dict[str, List[str]]:
    """Map canonical stage id -> expected output filenames, derived from the
    feature's approved upstream artefacts (not from the target directory).
    Profile-dependent stages are omitted except for the in-memory default."""
    def _dir(rel: str) -> str:
        return os.path.join(feature_root, "stages", rel, "output")

    out: Dict[str, List[str]] = {}
    out["01"] = ["usecase.md"]
    out["01a"] = ["responsibility-map.md"]

    usecase = os.path.join(_dir("01_usecase"), "usecase.md")
    if os.path.isfile(usecase):
        out["01b"] = [slugify(name) + "-chain.md"
                      for name in sorted(parse_scenario_names(usecase))]

    resp_map = os.path.join(_dir("01a_responsibility-map"),
                            "responsibility-map.md")
    concepts: List[str] = []
    if os.path.isfile(resp_map):
        concepts = [c for c in sorted(parse_responsibility_map(resp_map))
                    if c != "Web"]
        out["02"] = [c + ".concept.md" for c in concepts]

    out["04a"] = ["_NOT_APPLICABLE.md"]

    if concepts:
        out["03b"] = [c + ".data-model.md" for c in concepts]
        out["04b"] = [c + ".spec.md" for c in concepts]

    sync_specs = parse_syncs(_dir("03_syncs")) if os.path.isdir(_dir("03_syncs")) else []
    if sync_specs:
        out["03"] = [s.name + ".sync.md" for s in sync_specs]
        participating = set()
        for s in sync_specs:
            # A joined rule participates in every conjunct's concept, not
            # just the primary trigger.
            for concept in ([c.concept for c in s.conjuncts]
                            or [s.trigger_concept]):
                if concept:
                    participating.add(concept)
            participating.update(c for c, _ in s.then_targets)
        out["03a"] = [c + "-card.md" for c in sorted(participating)] + [
            "pattern-d-summary.md", "concept-matrix.md"]

    slug = feature_slug(feature_root)
    out["04c"] = [(slug or "flow") + ".feature"]
    out["04d-red"] = ["concept-test-derivation.md"]
    out["04d-green"] = ["green-evidence.md"]
    out["04e-red"] = ["sync-test-derivation.md"]
    out["04e-green"] = ["green-evidence.md"]
    out["05"] = ["trace.md", "smoke.md", "tracking.md"]
    return out


def normalize_outcome(name: str) -> str:
    """PascalCase -> SCREAMING_SNAKE_CASE, then uppercase."""
    s = name.strip()
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.upper()


def pascal(name: str) -> str:
    """PascalCase a token (for sync-name grammar)."""
    return "".join(part[:1].upper() + part[1:].lower() for part in name.split("-"))


def pascal_token(raw: str) -> str:
    """Convert a CLAD signature token to PascalCase for sync names.

    Identical to verify_implementation_parity.pascal_token: strips backticks/quote/
    leading `?`, splits on non-alphanumerics, then splits camel/acronym runs.
    """
    token = raw.strip().strip("`").strip('"').strip("'")
    token = token.lstrip("?")
    parts = []
    for chunk in re.split(r"[^A-Za-z0-9]+", token):
        if not chunk:
            continue
        parts.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", chunk))
    return "".join(part[:1].upper() + part[1:].lower() for part in parts)


def first_completion_token(completion: str) -> str:
    """First completion token, PascalCased (copied from verify_implementation_parity)."""
    for raw_part in re.split(r"[;,]", completion):
        part = raw_part.strip()
        if not part:
            continue
        if ":" in part:
            _, value = part.split(":", 1)
            value = value.strip()
            if value.startswith('"') or value.startswith("'"):
                return pascal_token(value)
            return pascal_token(part.split(":", 1)[0].split("(", 1)[0])
        return pascal_token(part.split("(", 1)[0])
    return ""


def completion_with_payload(outcome_raw: str) -> str:
    """PascalCase completion including any outcome payload.

    Two outcomes of one action may differ only in payload (`Released` vs
    `Released(blankFields)`); the sync stem must stay unique across them, so
    the payload joins the completion token (`...ReleasedBlankFields`). Shared
    by `generate_syncs` and `verify_implementation_parity` so the derived name
    cannot drift.
    """
    name = first_completion_token(outcome_raw)
    m = re.search(r"\(([^)]*)\)", outcome_raw or "")
    if not m:
        return name
    payload = "".join(
        word.capitalize() for word in re.split(r"[^A-Za-z0-9]+", m.group(1)) if word)
    if not payload or payload.lower() == name.lower():
        return name
    return name + payload


def sync_stem(then_concept: str, then_action: str, scope: str,
              conjuncts: List["Conjunct"], is_join: bool) -> str:
    """Mechanical sync stem (grammar v2 / join grammar).

    Single-trigger: `<Target><Action>[For<Scope>]When<C><A><Outcome>`.
    Joined rule:    `<Target><Action>[For<Scope>]WhenJoin<C1><A1><Out1>And<C2>...`
    in declared conjunct order (deterministic).
    """
    base = (pascal_token(then_concept) + pascal_token(then_action)
            + ("For" + scope if scope else ""))
    if is_join:
        # Payload-free completions per conjunct: joining every payload would
        # blow past the OS filename limit (NAME_MAX 255) for richer joins,
        # and the completion token is the documented grammar for a conjunct.
        parts = [
            pascal_token(c.concept) + pascal_token(c.action)
            + first_completion_token(c.outcome)
            for c in conjuncts
        ]
        return base + "WhenJoin" + "And".join(parts)
    if not conjuncts:
        return base + "When"
    c = conjuncts[0]
    return (base + "When" + pascal_token(c.concept) + pascal_token(c.action)
            + completion_with_payload(c.outcome))


def feature_scope_from_path(path: str) -> str:
    """The `For<Scope>` suffix derived from the feature folder slug (`UC-01-login` -> `Login`)."""
    parts = os.path.normpath(path).split(os.sep)
    if "features" not in parts:
        return ""
    index = parts.index("features")
    if index + 1 >= len(parts):
        return ""
    feature = parts[index + 1]
    match = re.match(r"UC-\d+-(.+)", feature)
    return pascal_token(match.group(1) if match else feature)
