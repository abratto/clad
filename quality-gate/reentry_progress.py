#!/usr/bin/env python3
"""Re-entry progress for iterative changes.

An active `_changes/<slug>.md` record declares an `Earliest re-entry stage` and
a `## Re-derivation order`. While it is active, `advance` must run the declared
stages IN ORDER — not the canonical next-stage chain — and must not mistake a
populated baseline stage for one re-derived during the change.

Progress lives in a sibling `_changes/<slug>.progress.json`. It is change-scoped
so an unrelated `advance` cannot clobber it (a stage `.gate-receipt.json` is
rewritten on every advance), and the receipt contract is left untouched.

`current_stage` returns the first declared stage not yet re-derived; `mark_done`
records one. A stage that is merely populated (the retained baseline) is NOT
`done` until the re-entry re-derives it, so stale downstream output cannot pass
as freshly derived.
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional

import clad_stages as cs
import verify_stage_sequence as vss

PROGRESS_SUFFIX = ".progress.json"
_ORDER_HEADER = "## Re-derivation order"
_STAGE_TOKEN = re.compile(r"\bStage\s+(\d+[a-z]?)\b")


def is_progress_file(name: str) -> bool:
    """True for a re-entry progress file (never a `_changes/` record)."""
    return name.endswith(PROGRESS_SUFFIX)


def _slug(change_path: str) -> str:
    return os.path.basename(change_path)[:-3]  # strip ".md"


def progress_path(change_path: str) -> str:
    return change_path[:-3] + PROGRESS_SUFFIX


def _section(text: str, header: str) -> str:
    if header not in text:
        return ""
    return text.split(header, 1)[1].split("\n## ", 1)[0]


def reentry_order(feature_root: str, change_path: str, reentry_stage: str) -> List[str]:
    """The stages a re-entry runs, in order.

    Prefers the stages the record's `## Re-derivation order` names, in order,
    deduplicated and validated against the current stage set. Falls back to the
    canonical suffix from the re-entry stage when the record names none (an
    older or terser record)."""
    with open(change_path, encoding="utf-8") as handle:
        text = handle.read()
    order: List[str] = []
    for raw in _STAGE_TOKEN.findall(_section(text, _ORDER_HEADER)):
        if cs.stage_by_id(raw) and raw not in order:
            order.append(raw)
    if not order:
        order = [s.id for s in cs.STAGES[cs.stage_index(reentry_stage):]]
    return order


def _read(change_path: str) -> Dict:
    path = progress_path(change_path)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def active_progress(feature_root: str) -> Optional[Dict]:
    """The single active re-entry's progress, or None when none is active."""
    change = vss.active_reentry_change(feature_root)
    if not change:
        return None
    reentry_stage, change_path = change
    order = reentry_order(feature_root, change_path, reentry_stage)
    done = [s for s in _read(change_path).get("done", []) if s in order]
    return {
        "slug": _slug(change_path),
        "change_path": change_path,
        "reentry_stage": reentry_stage,
        "order": order,
        "done": done,
    }


def remaining(progress: Dict) -> List[str]:
    return [s for s in progress["order"] if s not in progress["done"]]


def current_stage(feature_root: str) -> Optional[str]:
    """The stage a re-entry should run now: the first declared stage not yet
    re-derived. Returns None when no re-entry is active.

    When the order is exhausted (every declared stage re-derived) it returns the
    last declared stage, so a further advance re-runs it idempotently and reports
    the change complete rather than looping on the first."""
    progress = active_progress(feature_root)
    if not progress:
        return None
    todo = remaining(progress)
    if todo:
        return todo[0]
    return progress["order"][-1] if progress["order"] else progress["reentry_stage"]


def next_stage(feature_root: str) -> Optional[str]:
    """The declared stage after the current one, or None when the re-entry's
    order is exhausted (the change is complete). None also when no re-entry is
    active — callers then fall back to the canonical next-stage chain."""
    progress = active_progress(feature_root)
    if not progress:
        return None
    todo = remaining(progress)
    if len(todo) >= 2:
        return todo[1]
    return None


def done_stages(change_path: str) -> List[str]:
    """The stages a specific change record has re-derived (its progress file).

    Content-based (git-trackable), unlike a stage `.gate-receipt.json` mtime."""
    return list(_read(change_path).get("done", []))


def mark_done(feature_root: str, stage_id: str) -> None:
    """Record that the re-entry has re-derived `stage_id`."""
    progress = active_progress(feature_root)
    if not progress:
        return
    if stage_id in progress["order"] and stage_id not in progress["done"]:
        progress["done"].append(stage_id)
    with open(progress_path(progress["change_path"]), "w",
              encoding="utf-8") as handle:
        json.dump({
            "change": progress["slug"],
            "reentry_stage": progress["reentry_stage"],
            "order": progress["order"],
            "done": progress["done"],
        }, handle, indent=2)
        handle.write("\n")
