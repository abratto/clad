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

@dataclass
class ChainRow:
    """One row of a chain-table (the `# | When | Then | Inputs | Outcome | Why`
    shape). Column 0 is the row number; concept/action are normalised to
    slash notation. `outcome_base` is the outcome with parenthesised payload
    removed (`Found(userId)` -> `Found`), and `outcome_payload` is the raw
    parenthesised content (or None). `then_suffix` is the bracketed action
    suffix when present (`[200]`, `[401]`) — these mark terminal respond rows.
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


def _split_row(line: str) -> List[str]:
    return [c.strip() for c in line.split("|")]


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

        # Outcome column is backtick-quoted; take the first token.
        outcome_match = re.search(r"`([^`]+)`", outcome_col)
        outcome_raw = outcome_match.group(1) if outcome_match else ""
        outcome_base = re.sub(r"\(.*?\)", "", outcome_raw).strip()
        payload_match = re.search(r"\(([^)]*)\)", outcome_raw)
        outcome_payload = payload_match.group(1) if payload_match else None

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


def parse_sync(path: str) -> Optional[SyncSpec]:
    """Parse one *.sync.md file into its name, trigger, targets, and Pattern D flag."""
    if not os.path.isfile(path) or not path.endswith(".sync.md"):
        return None
    fname = os.path.basename(path)
    with open(path) as f:
        text = f.read()

    name_match = re.search(r"^sync\s+(\w+)", text, re.MULTILINE)
    name = name_match.group(1) if name_match else fname.replace(".sync.md", "")

    when_block = text.partition("when {")[2].partition("}")[0] if "when {" in text else ""
    then_block = text.partition("then {")[2].partition("}")[0] if "then {" in text else ""

    trigger_concept, trigger_action, trigger_outcome = "", "", ""
    when_main = re.search(r"(\w+)/(\w+)\s*:\s*\[([^\]]*)\]\s*=>\s*\[([^\]]*)\]", when_block)
    if when_main:
        trigger_concept = when_main.group(1)
        trigger_action = when_main.group(2)
        # Completion = first token on the right of the arrow.
        right = when_main.group(4).strip()
        outcome_m = re.match(r"([A-Za-z][A-Za-z0-9_]*)", right)
        trigger_outcome = outcome_m.group(1) if outcome_m else right

    then_targets: List[Tuple[str, str]] = []
    for m in re.finditer(r"([A-Za-z]+)/([A-Za-z]+)\s*:", then_block):
        then_targets.append((m.group(1), m.group(2)))

    cited: List[str] = re.findall(r"—\s+scenario\s+[\"`']([^\"`']+)[\"`']", text)

    # Pattern D = a concept-state read in the where block: `Concept: { ... }`
    where_block = text.partition("where {")[2].partition("}")[0] if "where {" in text else ""
    has_pattern_d = bool(re.search(r"[A-Za-z]+\s*:\s*\{", where_block))
    pattern_d_concepts = re.findall(r"([A-Za-z][A-Za-z0-9]*)\s*:\s*\{", where_block)

    return SyncSpec(
        name=name,
        filename=fname,
        trigger_concept=trigger_concept,
        trigger_action=trigger_action,
        trigger_outcome=trigger_outcome,
        then_targets=then_targets,
        cited_scenarios=cited,
        has_pattern_d=has_pattern_d,
        pattern_d_concepts=pattern_d_concepts,
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

def parse_scenario_names(usecase_path: str) -> Set[str]:
    names: Set[str] = set()
    with open(usecase_path) as f:
        for line in f:
            m = re.match(r"^### Scenario:\s+(.+)$", line.strip())
            if m:
                names.add(m.group(1).strip())
    return names


def parse_goals(path: str) -> Set[str]:
    goals: Set[str] = set()
    with open(path) as f:
        lines = f.readlines()
    in_table = False
    for line in lines:
        if line.strip().startswith("| Actor | Goal |"):
            in_table = True
            continue
        if in_table:
            if line.strip() == "" or line.startswith("##"):
                in_table = False
                continue
            if re.match(r"^\|[\s\-:]+\|", line):
                continue
            parts = _split_row(line)
            if len(parts) >= 3:
                goals.add(parts[2])
    return goals


# --------------------------------------------------------------------------
# Naming helpers shared by checks and generators
# --------------------------------------------------------------------------

def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


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
