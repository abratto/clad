#!/usr/bin/env python3
"""
artifact_parsers.py — shared parsers for CLAD markdown artefacts.

Single source of truth for reading the canonical artefact formats:

  - chain tables       (01b)  -> list of ChainRow
  - responsibility map (01a)  -> dict concept -> ResponsibilityMapEntry
  - concept specs      (02)   -> dict concept -> ConceptSpec
  - sync specs         (03)   -> list of SyncSpec
  - dependency cards   (03a)  -> dict concept -> set of actions
  - contracts              (04b)  -> dict (concept, action) -> outcomes
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
    origin: str = ""


# Column header fragments -> the field they supply. The Concepts table was
# extended (maintenance change `system-scope-concept-vocabulary`) with an
# `Origin` column; older maps have no such column. Resolve columns by header,
# never by position, so both shapes parse.
_RESP_COLUMN_MAP = (
    ("Concept", "concept"),
    ("Origin", "origin"),
    ("Owned state", "owned_state"),
    ("Owned actions", "owned_actions"),
    ("Notes", "notes"),
)


def _resp_columns(header_parts: List[str]) -> Dict[int, str]:
    columns: Dict[int, str] = {}
    for idx, cell in enumerate(header_parts):
        label = cell.strip()
        for fragment, field in _RESP_COLUMN_MAP:
            if label.startswith(fragment):
                columns[idx] = field
                break
    return columns


def parse_responsibility_map(path: str) -> Dict[str, ResponsibilityMapEntry]:
    entries: Dict[str, ResponsibilityMapEntry] = {}
    with open(path) as f:
        columns: Dict[int, str] = {}
        in_table = False
        for line in f:
            if line.lstrip().startswith("| Concept |") and "Owned state" in line:
                columns = _resp_columns(_split_row(line))
                in_table = True
                continue
            if in_table:
                if re.match(r"^\|[\s\-:]+\|", line):
                    continue
                if not line.startswith("|"):
                    in_table = False
                    continue
                parts = _split_row(line)
                fields: Dict[str, str] = {}
                for idx, field in columns.items():
                    if idx < len(parts):
                        fields[field] = parts[idx]
                concept = fields.get("concept", "").strip("`").strip()
                if not concept:
                    continue
                entries[concept] = ResponsibilityMapEntry(
                    concept=concept,
                    owned_state=fields.get("owned_state", ""),
                    owned_actions=re.findall(r"`([^`]+)`",
                                             fields.get("owned_actions", "")),
                    notes=fields.get("notes", ""),
                    origin=fields.get("origin", "").strip("`").strip(),
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


def concept_spec_paths(concept_dirs: List[str]) -> Dict[str, str]:
    """Map concept name -> spec path across one or more concept dirs.

    Earlier dirs shadow later ones by concept name, so a feature's own Stage-02
    proposal (NEW/EXTEND) shadows the canonical corpus spec of the same name.
    Non-existent dirs are ignored.
    """
    out: Dict[str, str] = {}
    for directory in concept_dirs:
        if not os.path.isdir(directory):
            continue
        for fname in sorted(os.listdir(directory)):
            if not fname.endswith(".concept.md"):
                continue
            out.setdefault(fname[: -len(".concept.md")],
                           os.path.join(directory, fname))
    return out


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


def parse_concept_actions_multi(concept_dirs: List[str]) -> Set[str]:
    """Set of Concept/action merged across one or more concept dirs.

    Earlier dirs shadow later ones by concept name (see concept_spec_paths)."""
    actions: Set[str] = set()
    for concept, path in concept_spec_paths(concept_dirs).items():
        for a in parse_concept(path).actions:
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
    record_collect_forms: List[str] = field(default_factory=list)


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

# Record-form collect (maintenance/engine-record-collect.md): a binding subset
# per frame — `collect ( ?a ?b as ?rows )` / `collect by ?key ( ?a ?b as ?rows )`.
# Two or more variables before `as`; one variable is the value-collect form.
_RECORD_COLLECT_RE = re.compile(
    r"\bcollect\b\s*(?:distinct\b\s*)?(?:by\s+\?\w+\s*)?"
    r"\(\s*\?\w+(?:\s+\?\w+)+ as\s+\?\w+\s*\)")


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
    # (stateRead("Concept", ...) / subjects("Concept", ...) / fanOut(?, "Concept", ...))
    # and the negative state pattern (absent(...), a D- read: it consults
    # state and binds nothing — maintenance/engine-absent-state-guard.md):
    # the where block may use the fluent factories instead of the
    # `Concept: { ... }` prose form; detect both so Pattern-D audits
    # (Stage 03a dependency cards) see the reads.
    for c in re.findall(r"(?:stateRead|subjects)\s*\(\s*\"([A-Za-z][A-Za-z0-9]*)\"", where_block) \
            + re.findall(r"fanOut\s*\(\s*\"[^\"]*\"\s*,\s*\"([A-Za-z][A-Za-z0-9]*)\"", where_block) \
            + re.findall(r"absent\s*\(\s*\"?([A-Za-z][A-Za-z0-9]*)\"?", where_block):
        if c not in pattern_d_concepts:
            pattern_d_concepts.append(c)
    has_pattern_d = has_pattern_d or bool(pattern_d_concepts)
    # Declarative collect forms (collect / collect distinct / collect by).
    collect_forms = [m.group(0).strip() for m in _COLLECT_RE.finditer(where_block)]
    # Record-form collect (a binding subset per frame).
    record_collect_forms = [m.group(0).strip()
                            for m in _RECORD_COLLECT_RE.finditer(where_block)]
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
        record_collect_forms=record_collect_forms,
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
# contracts (Stage 04b)
# --------------------------------------------------------------------------

def parse_spec_actions(contract_dir: str) -> Set[str]:
    actions: Set[str] = set()
    if not os.path.isdir(contract_dir):
        return actions
    for fname in sorted(os.listdir(contract_dir)):
        if not fname.endswith(".contract.md"):
            continue
        concept = fname.replace(".contract.md", "")
        with open(os.path.join(contract_dir, fname)) as f:
            for line in f:
                m = re.match(r"^###\s+`(\w+)\(", line.strip())
                if m:
                    actions.add(f"{concept}/{m.group(1)}")
    return actions


def merge_by_concept(contract_dirs, parse_one):
    """Merge `parse_one(dir)` across contract dirs, earlier dirs shadowing later.

    A feature emits a contract only for a concept it introduces or extends; a
    REUSED concept binds the canonical contract in the corpus (R22). Any gate
    that judges something *outside* the feature's own contracts — a chain, a Java
    test file — must therefore see this shadowed union, not one directory.
    """
    merged, owned = {}, set()
    for directory in contract_dirs:
        if not os.path.isdir(directory):
            continue
        for key, value in parse_one(directory).items():
            concept = key[0] if isinstance(key, tuple) else key
            if concept in owned:
                continue                      # an earlier dir owns this concept
            merged[key] = value
        for fname in sorted(os.listdir(directory)):
            if fname.endswith(".contract.md"):
                owned.add(fname.replace(".contract.md", ""))
    return merged


def _actions_by_concept(contract_dir: str):
    out = {}
    if not os.path.isdir(contract_dir):
        return out
    for fname in sorted(os.listdir(contract_dir)):
        if not fname.endswith(".contract.md"):
            continue
        with open(os.path.join(contract_dir, fname), encoding="utf-8") as handle:
            text = handle.read()
        out[fname.replace(".contract.md", "")] = set(
            re.findall(r"^###\s+`(\w+)\(", text, re.MULTILINE))
    return out


def contract_actions(contract_dirs) -> Set[str]:
    """`Concept/action` across contract dirs, earlier ones shadowing later."""
    merged = merge_by_concept(contract_dirs, _actions_by_concept)
    return {f"{concept}/{action}" for concept, actions in merged.items()
            for action in actions}


def parse_spec_outcomes_multi(contract_dirs):
    """`{(concept, action): outcomes}` across dirs, earlier dirs shadowing later.

    The outcome counterpart of :func:`contract_actions`: a reused concept's
    outcomes come from its canonical contract, an extended one's from the
    feature's own.
    """
    return merge_by_concept(contract_dirs, parse_spec_outcomes)


def parse_spec_outcomes(contract_dir: str) -> Dict[Tuple[str, str], Set[str]]:
    """{(concept, action): set(outcome strings)} from contract files."""
    specs: Dict[Tuple[str, str], Set[str]] = {}
    if not os.path.isdir(contract_dir):
        return specs
    for fname in sorted(os.listdir(contract_dir)):
        if not fname.endswith(".contract.md"):
            continue
        concept = fname.replace(".contract.md", "")
        path = os.path.join(contract_dir, fname)
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
    # A `## Out of scope` section repeats the `| Actor | Goal |` header but
    # carries no `In scope?` column; without this guard its rows were counted
    # as in-scope goals (observed as "19 in-scope goals" throughout the conduit
    # rebuild). Skip any table under an out-of-scope heading.
    out_of_scope = False
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith("##"):
            out_of_scope = "out of scope" in line.lower()
            in_table = False
            continue
        if out_of_scope:
            continue
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


def _default_corpus_dir(feature_root: str) -> str:
    """`features/_system/concepts`, sibling of the feature folder."""
    return os.path.join(os.path.dirname(os.path.abspath(feature_root)),
                        "_system", "concepts")


def feature_model_concepts(feature_root: str, corpus_dir: str = "") -> List[str]:
    """Concepts this feature must produce a **conceptual data model** for.

    The canonical model lives with the canonical concept
    (`features/_system/concepts/<Name>.data-model.md`), so a feature derives one
    only when it introduces or CHANGES the concept's state:

      * `new`                                     -> yes
      * `extends:*` whose `## State` differs from the canonical spec -> yes
      * `reused`, or an extend leaving state unchanged               -> no
      * a legacy map with no `Origin` column      -> every concept (pre-Model-B
        expectation, kept for compatibility).

    Single source of truth for the 03b file manifest and `generate_data_model`.
    """
    resp = os.path.join(feature_root, "stages", "01a_responsibility-map",
                        "output", "responsibility-map.md")
    if not os.path.isfile(resp):
        return []
    entries = parse_responsibility_map(resp)
    corpus = corpus_dir or _default_corpus_dir(feature_root)
    out: List[str] = []
    for concept, entry in sorted(entries.items()):
        if concept == "Web":
            continue
        origin = (entry.origin or "").strip().lower()
        if not origin or origin.startswith("new"):
            out.append(concept)
        elif origin.startswith("extend") and _state_changed(
                feature_root, concept, corpus):
            out.append(concept)
    return out


def _state_changed(feature_root: str, concept: str, corpus: str) -> bool:
    """True when this feature's proposal changes the concept's `## State`."""
    proposal = os.path.join(feature_root, "stages", "02_concepts", "output",
                            concept + ".concept.md")
    canonical = os.path.join(corpus, concept + ".concept.md") if corpus else ""
    if not os.path.isfile(canonical):
        return True                      # no canonical spec — state is new
    if not os.path.isfile(proposal):
        return False
    return (parse_concept(proposal).state_lines
            != parse_concept(canonical).state_lines)


def feature_contract_concepts(feature_root: str) -> List[str]:
    """Concepts this feature must produce a **concept contract** for.

    The canonical contract lives with the canonical concept
    (`features/_system/concepts/<Name>.contract.md`), so a feature derives one
    only when it introduces or EXTENDS a concept — an extend adds or changes an
    action, so the contract moves with it. A `reused` concept binds the
    canonical contract; a legacy map (no `Origin`) keeps one contract per
    concept.

    Single source of truth for the 04b file manifest and `generate_contract`.
    """
    resp = os.path.join(feature_root, "stages", "01a_responsibility-map",
                        "output", "responsibility-map.md")
    if not os.path.isfile(resp):
        return []
    out: List[str] = []
    for concept, entry in sorted(parse_responsibility_map(resp).items()):
        if concept == "Web":
            continue
        origin = (entry.origin or "").strip().lower()
        if not origin or origin.startswith("new") or origin.startswith("extend"):
            out.append(concept)
    return out


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
        entries = parse_responsibility_map(resp_map)
        concepts = [c for c in sorted(entries) if c != "Web"]
        if any(entries[c].origin for c in concepts):
            # Model B map: Stage 02 always emits bindings, plus a proposal for
            # every NEW/EXTEND concept. REUSE rows bind only (no spec copy).
            proposals = [
                c for c in concepts
                if entries[c].origin.lower().startswith(("new", "extend"))
            ]
            out["02"] = ["concept-bindings.md"] + [
                c + ".concept.md" for c in proposals]
        else:
            # Legacy map without an Origin column: one spec per concept.
            out["02"] = [c + ".concept.md" for c in concepts]

    out["04a"] = ["_NOT_APPLICABLE.md"]

    model_concepts = feature_model_concepts(feature_root)
    if model_concepts:
        out["03b"] = [c + ".data-model.md" for c in model_concepts]
        out["04b"] = [c + ".contract.md" for c in feature_contract_concepts(feature_root)]

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


#: Highest escalation level `sync_stem` produces (see its docstring).
SYNC_STEM_MAX_LEVEL = 3


def sync_stem(then_concept: str, then_action: str,
              conjuncts: List["Conjunct"], is_join: bool,
              level: int = 0, with_payload: bool = False,
              route: str = "") -> str:
    """Mechanical sync stem (grammar v3, action-first).

    Level 0 (the default) names the effect and its trigger by ACTION only:

        single trigger: `<TargetAction>[For<Route>]When<TriggerAction><Completion>`
        joined rule:    `<TargetAction>WhenJoin<A1><Out1>And<A2><Out2>...`
                        (declared conjunct order — deterministic)

    A sync is *coordination*, not a concept's property — it can involve several
    concepts — so concept tokens are omitted unless needed to disambiguate.
    `level` adds them back deterministically when two stems would collide
    within one sync pack:

        1 -> + target concept
        2 -> + trigger concept
        3 -> + both

    The completion is named by its BASE token only (`Routed`, not
    `RoutedRefName`) — the carried fields are body-visible and never needed to
    read the name. `with_payload=True` is the last-resort disambiguator for two
    outcomes of one action that differ only in payload
    (`Released` vs `Released(blankFields)`).

    **`For<Route>`.** A route-scoped bootstrap carries the route it matches:
    `VerifyForReturnsWhenRequestRouted`. Two use cases may bootstrap the *same*
    target action on *different* routes (`memberEnrolment.verify` after a borrow
    request and after a return request), and nothing else in the name separates
    them — so without the route the app registers two rules with one name and
    `causedBySync` can no longer say which fired.

    The pre-v0.6 `For<Scope>` component was **not** this: it was derived from the
    *feature slug*, so every sync in a use case carried the same value and it
    could never disambiguate anything. That was the right thing to remove; the
    route is a real discriminator within one app, which the slug never was.
    """
    target = pascal_token(then_action)
    if level in (1, 3):
        target = pascal_token(then_concept) + target
    if route:
        # The route is a real discriminator: two use cases may bootstrap the same
        # target action on different routes.
        target += "For" + pascal_token(route)
    if is_join:
        # Payload-free completions per conjunct: joining every payload would
        # blow past the OS filename limit (NAME_MAX 255) for richer joins,
        # and the completion token is the documented grammar for a conjunct.
        parts = []
        for c in conjuncts:
            token = pascal_token(c.action) + first_completion_token(c.outcome)
            if level in (2, 3):
                token = pascal_token(c.concept) + token
            parts.append(token)
        return target + "WhenJoin" + "And".join(parts)
    if not conjuncts:
        return target + "When"
    c = conjuncts[0]
    completion = (completion_with_payload(c.outcome) if with_payload
                  else first_completion_token(c.outcome))
    trigger = pascal_token(c.action) + completion
    if level in (2, 3):
        trigger = pascal_token(c.concept) + trigger
    return target + "When" + trigger


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
