#!/usr/bin/env python3
"""
clad_stages.py — Canonical per-UC stage model for the CLAD workflow.

This module is the single source of truth for:
  - the ordered list of per-UC stages (01 -> 05),
  - each stage's output directory and CONTEXT.md path (relative to a feature
    root),
  - which human gate (if any) must be approved before advancing past a stage,
  - the deterministic cross-stage checks that apply when a stage completes.

Both `verify_stage_sequence.py` (the entry/sequence guard) and `advance.py`
(the gate-driven advance CLI) import this module so the stage order and the
checks map are defined in exactly one place. Do not duplicate this list.

Scope note: this module models the *per-UC* stages only. The system-level
Stage 00 (`features/_system/stages/00_actor-goal/`) runs once per brief and is
not part of the per-feature advance loop; its `goals.md` is consumed as an
input by some checks.
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# --------------------------------------------------------------------------
# Check specification
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Check:
    """One deterministic cross-stage check bound to a stage.

    `script` is the quality-gate script filename. `build_args` receives the
    absolute feature root and returns the argv list (excluding the interpreter
    and the script path). `requires` is a list of absolute paths (files or
    directories) that must exist and be non-empty for the check to run; if any
    is missing the check is reported as `skip` (inputs not present) rather than
    failing.
    """

    name: str
    script: str
    build_args: Callable[[str], List[str]]
    requires: Callable[[str], List[str]]


# --------------------------------------------------------------------------
# Path helpers (all relative to an absolute feature root)
# --------------------------------------------------------------------------

def output_dir(feature_root: str, rel: str) -> str:
    return os.path.join(feature_root, "stages", rel, "output")


def _usecase(feature_root: str) -> str:
    return os.path.join(feature_root, "stages", "01_usecase", "output", "usecase.md")


def _resp_map(feature_root: str) -> str:
    return os.path.join(
        feature_root, "stages", "02a_responsibility-map", "output",
        "responsibility-map.md")


def _goals(feature_root: str) -> str:
    """System-level goals.md lives under features/_system, a sibling of the
    UC feature folder."""
    features_dir = os.path.dirname(feature_root)
    return os.path.join(
        features_dir, "_system", "stages", "00_actor-goal", "output", "goals.md")


def _dir(rel: str) -> Callable[[str], str]:
    return lambda root: output_dir(root, rel)


# Convenience references to the per-stage output directories.
CHAIN_DIR = _dir("02b_chain-table")
CONCEPT_DIR = _dir("02_concepts")
SYNC_DIR = _dir("03_syncs")
DEP_DIR = _dir("03a_dependency-review")
DATA_DIR = _dir("03b_data-model")


def _spec_dir(feature_root: str) -> str:
    return os.path.join(
        feature_root, "stages", "04_implement", "04b_spec", "output")


# --------------------------------------------------------------------------
# Stage specification
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Stage:
    id: str
    label: str
    # Directory (relative to feature root) that contains this stage's CONTEXT.md
    context_dir: str
    # Human gate number (1/2/3) that must be approved BEFORE advancing past
    # this stage, or None for auto-advance stages.
    gate_after: Optional[int] = None
    checks: List[Check] = field(default_factory=list)

    def output_dir(self, feature_root: str) -> str:
        return os.path.join(feature_root, "stages", self.context_dir, "output")

    def context_path(self, feature_root: str) -> str:
        return os.path.join(feature_root, "stages", self.context_dir, "CONTEXT.md")


# --------------------------------------------------------------------------
# Check definitions (only checks whose inputs are plain markdown artefacts and
# therefore runnable profile-agnostically at design time are wired here).
# Profile-specific checks (Java test roots, Gherkin discovery paths, parity
# scripts) remain the responsibility of the local pre-commit gate / CI, which
# have the profile config available.
# --------------------------------------------------------------------------

_SCENARIO_COVERAGE = Check(
    name="scenario_coverage",
    script="verify_scenario_coverage.py",
    build_args=lambda r: [
        "--goals", _goals(r),
        "--usecase", _usecase(r),
        "--chain-dir", CHAIN_DIR(r),
        "--sync-dir", SYNC_DIR(r),
    ],
    requires=lambda r: [_goals(r), _usecase(r), CHAIN_DIR(r), SYNC_DIR(r)],
)

_SYNC_MATRIX = Check(
    name="sync_matrix",
    script="verify_sync_matrix.py",
    build_args=lambda r: [
        "--sync-dir", SYNC_DIR(r),
        "--chain-dir", CHAIN_DIR(r),
    ],
    requires=lambda r: [SYNC_DIR(r)],
)

_DATA_MODEL = Check(
    name="data_model",
    script="verify_data_model.py",
    build_args=lambda r: [
        "--data-dir", DATA_DIR(r),
        "--concept-dir", CONCEPT_DIR(r),
    ],
    requires=lambda r: [DATA_DIR(r), CONCEPT_DIR(r)],
)

_SPEC_PARITY = Check(
    name="spec_parity",
    script="verify_spec_parity.py",
    build_args=lambda r: [
        "--concept-dir", CONCEPT_DIR(r),
        "--spec-dir", _spec_dir(r),
    ],
    requires=lambda r: [CONCEPT_DIR(r), _spec_dir(r)],
)

_OUTCOME_ALIGNMENT = Check(
    name="outcome_alignment",
    script="verify_outcome_alignment.py",
    build_args=lambda r: [
        "--chain-dir", CHAIN_DIR(r),
        "--spec-dir", _spec_dir(r),
    ],
    requires=lambda r: [CHAIN_DIR(r), _spec_dir(r)],
)

_ACTION_CHAIN = Check(
    name="action_chain",
    script="verify_action_chain.py",
    build_args=lambda r: [
        "--resp-map", _resp_map(r),
        "--chain-dir", CHAIN_DIR(r),
        "--concept-dir", CONCEPT_DIR(r),
        "--sync-dir", SYNC_DIR(r),
        "--dep-dir", DEP_DIR(r),
        "--spec-dir", _spec_dir(r),
    ],
    requires=lambda r: [
        _resp_map(r), CHAIN_DIR(r), CONCEPT_DIR(r), SYNC_DIR(r), DEP_DIR(r),
        _spec_dir(r),
    ],
)


# --------------------------------------------------------------------------
# Profile-aware checks — require implementation paths from clad.properties.
# These checks skip automatically when clad.properties is absent or the
# relevant path keys are unset, making them safe to wire into the
# design-time advance pipeline for all profiles.
# --------------------------------------------------------------------------

def _sync_impl_dir(feature_root: str) -> str:
    return _prop_path(feature_root, "sync.impl.dir")

def _concept_impl_dir(feature_root: str) -> str:
    return _prop_path(feature_root, "concept.impl.dir")

def _test_source_root(feature_root: str) -> str:
    return _prop_path(feature_root, "test.source.root")

def _features_dir(feature_root: str) -> str:
    return os.path.dirname(feature_root)

def _test_command(feature_root: str) -> str:
    return _prop(feature_root, "test.command")

_SYNC_ROUTE_FILTERS = Check(
    name="sync_route_filters",
    script="verify_sync_route_filters.py",
    build_args=lambda r: [
        "--sync-impl-dir", _sync_impl_dir(r),
    ],
    requires=lambda r: [_sync_impl_dir(r)],
)

_IMPL_PARITY = Check(
    name="implementation_parity",
    script="verify_implementation_parity.py",
    build_args=lambda r: [
        "--sync-impl-dir", _sync_impl_dir(r),
        "--concept-impl-dir", _concept_impl_dir(r),
        "--features-dir", _features_dir(r),
    ],
    requires=lambda r: [_sync_impl_dir(r)],
)

_SYNC_IMPL_PARITY = Check(
    name="sync_implementation_parity",
    script="verify_sync_implementation_parity.py",
    build_args=lambda r: [
        "--sync-impl-dir", _sync_impl_dir(r),
        "--features-dir", _features_dir(r),
    ],
    requires=lambda r: [_sync_impl_dir(r)],
)

_FIELD_ASSERTIONS = Check(
    name="concept_field_assertions",
    script="verify_concept_field_assertions.py",
    build_args=lambda r: [
        "--spec-dir", _spec_dir(r),
        "--test-source-root", _test_source_root(r),
    ],
    requires=lambda r: [_spec_dir(r), _test_source_root(r)],
)

_CUCUMBER_GREEN = Check(
    name="cucumber_green",
    script="verify_cucumber_green.py",
    build_args=lambda r: [
        "--feature-root", _features_dir(r),
        "--test-command", _test_command(r),
    ],
    requires=lambda r: [r for r in [_features_dir(r)]
                        if os.path.isdir(r)],
)

# File-manifest checks for stages with predictable single-file outputs.
# Stages with variable outputs use other checks or CONTEXT.md-level
# verify_file_manifest.py invocations.

_FILE_01 = Check(
    name="file_manifest",
    script="verify_file_manifest.py",
    build_args=lambda r: [
        "--dir", output_dir(r, "01_usecase"),
        "--expected", "usecase.md",
    ],
    requires=lambda r: [output_dir(r, "01_usecase")],
)

_FILE_02A = Check(
    name="file_manifest",
    script="verify_file_manifest.py",
    build_args=lambda r: [
        "--dir", output_dir(r, "02a_responsibility-map"),
        "--expected", "responsibility-map.md",
    ],
    requires=lambda r: [output_dir(r, "02a_responsibility-map")],
)


# --------------------------------------------------------------------------
# The canonical per-UC stage order.
# --------------------------------------------------------------------------

STAGES: List[Stage] = [
    Stage("01", "Use case", "01_usecase",
          checks=[_FILE_01]),
    Stage("02a", "Responsibility map", "02a_responsibility-map",
          checks=[_FILE_02A]),
    Stage("02b", "Chain table", "02b_chain-table", gate_after=1),
    Stage("02", "Concept specs", "02_concepts"),
    Stage("03", "Syncs", "03_syncs", checks=[_SCENARIO_COVERAGE, _SYNC_MATRIX]),
    Stage("03a", "Dependency review", "03a_dependency-review",
          checks=[_SYNC_ROUTE_FILTERS]),
    Stage("03b", "Data model", "03b_data-model", gate_after=2, checks=[_DATA_MODEL]),
    Stage("04a", "Storage mapping", "04_implement/04a_storage-mapping"),
    Stage("04b", "SPEC", "04_implement/04b_spec",
          checks=[_SPEC_PARITY, _OUTCOME_ALIGNMENT, _ACTION_CHAIN]),
    Stage("04c", "Flow tests", "04_implement/04c_flow-tests", gate_after=3,
          checks=[_CUCUMBER_GREEN]),
    Stage("04d", "Concept TDD", "04_implement/04d_concept-tdd",
          checks=[_FIELD_ASSERTIONS]),
    Stage("04e", "Sync TDD", "04_implement/04e_sync-tdd",
          checks=[_IMPL_PARITY, _SYNC_IMPL_PARITY]),
    Stage("05", "Verify", "05_verify"),
]

GATE_LABELS = {
    1: "Requirements",
    2: "Architecture",
    3: "Executable spec",
}


# --------------------------------------------------------------------------
# Lookup helpers
# --------------------------------------------------------------------------

def stage_by_id(stage_id: str) -> Optional[Stage]:
    for s in STAGES:
        if s.id == stage_id:
            return s
    return None


def stage_index(stage_id: str) -> int:
    for i, s in enumerate(STAGES):
        if s.id == stage_id:
            return i
    return -1


def next_stage(stage_id: str) -> Optional[Stage]:
    idx = stage_index(stage_id)
    if idx < 0 or idx + 1 >= len(STAGES):
        return None
    return STAGES[idx + 1]


def dir_is_populated(path: str) -> bool:
    """True if `path` is a directory containing at least one non-hidden,
    non-placeholder file (recursively)."""
    if not os.path.isdir(path):
        return False
    for root, _dirs, files in os.walk(path):
        for f in files:
            if f.startswith("."):
                continue
            if f in ("_.gitkeep", ".gitkeep", ".gitkeep.md"):
                continue
            return True
    return False


def relpath(path: str, start: Optional[str] = None) -> str:
    """Best-effort repo-relative path for display."""
    try:
        return os.path.relpath(path, start or os.getcwd())
    except ValueError:
        return path


# --------------------------------------------------------------------------
# Profile-aware configuration (reads clad.properties)
# --------------------------------------------------------------------------

def _repo_root(feature_root: str) -> str:
    return os.path.dirname(os.path.dirname(feature_root))


def _read_config(feature_root: str) -> Dict[str, str]:
    """Read clad.properties as a flat dict of key -> value.
    Unprefixed keys (in the [DEFAULT] section) are stored as-is.
    Section-prefixed keys use `section.key` notation.
    """
    path = os.path.join(_repo_root(feature_root), "clad.properties")
    result: Dict[str, str] = {}
    if not os.path.exists(path):
        return result
    cp = configparser.ConfigParser()
    cp.read(path)
    for key, value in cp.defaults().items():
        result[key] = value
    for section in cp.sections():
        for key, value in cp.items(section):
            result[f"{section}.{key}"] = value
    return result


def _prop_path(feature_root: str, key: str) -> str:
    """Read a repo-root-relative path property and resolve to absolute.
    Returns an empty string if the property is not set or the path does not
    exist, causing downstream checks to skip (empty-string paths never exist).
    """
    cfg = _read_config(feature_root)
    value = cfg.get(key)
    if not value:
        return ""
    resolved = os.path.join(_repo_root(feature_root), value)
    if not os.path.exists(resolved):
        return ""
    return resolved


def _prop(feature_root: str, key: str) -> str:
    """Read a plain string property from clad.properties."""
    return _read_config(feature_root).get(key, "")
