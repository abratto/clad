#!/usr/bin/env python3
"""Enumerate the terminal branches of a Stage 01b chain table.

A chain table is an FSM: each row is a `When -> Then` edge, and a path from the
`Web.request` root to a `Web.respond` terminal is one executable branch. The
acceptance-spec and trace generators use these paths instead of flattening every
row (which produced a single 16-token "chain" that could never match a real
flow).

Joins (`When` with `∧`) fire only when every conjunct state is already on the
path; the row that completed last is the current state. The traversal is
deterministic (rows in table order), de-duplicated, and cycle-safe.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import artifact_parsers as ap


State = Tuple[str, str, str]  # concept, action, normalized outcome


@dataclass(frozen=True)
class ChainPath:
    tokens: List[str]
    status: str
    terminal_row: int
    label: str = ""

    @property
    def is_success(self) -> bool:
        return self.status.startswith("2")


def _payload_base(outcome: str) -> str:
    return re.sub(r"\(.*?\)", "", outcome or "").strip()


def _normalized(outcome: str) -> str:
    return ap.normalize_outcome(_payload_base(outcome))


def _source_states(row: ap.ChainRow) -> List[State]:
    return [(conjunct.concept, conjunct.action,
             _normalized(conjunct.outcome))
            for conjunct in row.conjuncts]


def _result_state(row: ap.ChainRow) -> State:
    return (row.then_concept, row.then_action, _normalized(row.outcome_base))


def _token(row: ap.ChainRow) -> str:
    return (f"{row.then_concept}/{row.then_action}"
            f"[{_normalized(row.outcome_base)}]")


def _terminal_token(row: ap.ChainRow) -> str:
    outcome = _normalized(row.outcome_base) or "SENT"
    return f"Web.respond[{outcome}]"


def _status(row: ap.ChainRow) -> str:
    if row.then_suffix:
        match = re.search(r"\d+", row.then_suffix)
        if match:
            return match.group(0)
    return ""


def _label(row: ap.ChainRow) -> str:
    return (row.why or row.inputs or f"row {row.row_num}").strip()


def _legacy_path(rows: List[ap.ChainRow]) -> List[ChainPath]:
    """Fallback: one path through every row, for legacy/irregular tables."""
    tokens: List[str] = []
    terminal = None
    for row in rows:
        if row.then_concept == "Web" and row.then_action == "request":
            tokens.append(f"Web.request[{_normalized(row.outcome_base)}]")
            continue
        if row.then_concept == "Web" and row.then_action == "respond":
            tokens.append(_terminal_token(row))
            terminal = row
            continue
        tokens.append(_token(row))
    if terminal is None:
        return []
    return [ChainPath(tokens, _status(terminal), terminal.row_num,
                      _label(terminal))]


def enumerate_paths(rows: List[ap.ChainRow]) -> List[ChainPath]:
    """Return every root-to-terminal branch in `rows` (deduplicated)."""
    if not rows:
        return []
    roots = [row for row in rows
             if row.then_concept == "Web" and row.then_action == "request"]
    if not roots:
        return _legacy_path(rows)

    paths: List[ChainPath] = []
    seen: Set[Tuple[str, ...]] = set()

    def walk(state: State, path_states: Set[State], tokens: List[str],
             used: Set[int]) -> None:
        for row in rows:
            if row.row_num in used:
                continue
            if row.then_concept == "Web" and row.then_action == "request":
                continue
            sources = _source_states(row)
            if not sources:
                continue
            if len(sources) == 1:
                if sources[0] != state:
                    continue
            else:
                if state not in sources:
                    continue
                if not all(source in path_states for source in sources):
                    continue

            next_used = used | {row.row_num}
            if row.then_concept == "Web" and row.then_action == "respond":
                terminal_tokens = tokens + [_terminal_token(row)]
                key = tuple(terminal_tokens)
                if key not in seen:
                    seen.add(key)
                    paths.append(ChainPath(
                        terminal_tokens, _status(row), row.row_num, _label(row)))
                continue

            result = _result_state(row)
            if result in path_states:
                continue  # cycle
            walk(result, path_states | {result},
                 tokens + [_token(row)], next_used)

    for root in roots:
        root_token = f"Web.request[{_normalized(root.outcome_base)}]"
        state = _result_state(root)
        walk(state, {state}, [root_token], {root.row_num})

    if not paths:
        return _legacy_path(rows)
    paths.sort(key=lambda path: (path.terminal_row, path.tokens))
    return paths


def success_path(paths: List[ChainPath]) -> Optional[ChainPath]:
    """The first 2xx path, else the first path."""
    for path in paths:
        if path.is_success:
            return path
    return paths[0] if paths else None
