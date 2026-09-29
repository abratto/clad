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

import os
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import artifact_parsers as ap


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
    skip_in_artefact_gate: bool = False


# --------------------------------------------------------------------------
# Path helpers (all relative to an absolute feature root)
# --------------------------------------------------------------------------

def output_dir(feature_root: str, rel: str) -> str:
    return os.path.join(feature_root, "stages", rel, "output")


def _usecase(feature_root: str) -> str:
    return os.path.join(feature_root, "stages", "01_usecase", "output", "usecase.md")


def _resp_map(feature_root: str) -> str:
    return os.path.join(
        feature_root, "stages", "01a_responsibility-map", "output",
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
CHAIN_DIR = _dir("01b_chain-table")
# Deprecated for concept-spec resolution: prefer `concept_source_dirs()` — the
# effective concept source is the UNION of this feature's proposals and the
# canonical corpus (maintenance change `system-scope-concept-vocabulary`, M1).
# Kept for backward compatibility with derived repos and older scripts.
CONCEPT_DIR = _dir("02_concepts")
SYNC_DIR = _dir("03_syncs")
DEP_DIR = _dir("03a_dependency-review")
DATA_DIR = _dir("03b_data-model")


def _contract_dir(feature_root: str) -> str:
    return os.path.join(
        feature_root, "stages", "04_implement", "04b_contract", "output")


def _concept_corpus_dir(feature_root: str) -> str:
    """The system-scope concept corpus (maintenance change
    `system-scope-concept-vocabulary`, decision D2).

    Resolved through the repo-root-relative `concepts.dir` property, defaulting
    to `features/_system/concepts`. Returns '' when the property points nowhere
    and the default directory does not exist (a legacy feature)."""
    corpus = _prop_path(feature_root, "concepts.dir")
    if corpus:
        return corpus
    default = os.path.join(_repo_root(feature_root), "features", "_system",
                           "concepts")
    return default if os.path.isdir(default) else ""


def concept_source_dirs(feature_root: str) -> List[str]:
    """Ordered concept-spec source dirs for a feature (decision D5 / M1).

    A feature's own Stage-02 output (its NEW/EXTEND proposals) shadows the
    canonical corpus by concept name, so it is listed FIRST. When no corpus
    exists (legacy / pre-Model-B feature) the result is just the feature's own
    `02_concepts/output`, which is exactly the old behaviour."""
    dirs = [output_dir(feature_root, "02_concepts")]
    corpus = _concept_corpus_dir(feature_root)
    if corpus:
        dirs.append(corpus)
    return dirs


def _concept_source_requires(feature_root: str) -> List[str]:
    """`requires` inputs for concept-reading checks.

    The feature's own Stage-02 output is always listed, so the check runs even
    for a project's FIRST feature whose canonical corpus is still empty.
    Requiring the corpus dir unconditionally made every concept check silently
    `skip` in that case — a false green (experiment defect D8). The corpus is
    required only once it is populated.
    """
    dirs = [output_dir(feature_root, "02_concepts")]
    corpus = _concept_corpus_dir(feature_root)
    if corpus and dir_is_populated(corpus):
        dirs.append(corpus)
    return dirs


def feature_concept_names(feature_root: str) -> List[str]:
    """The concepts THIS feature uses, from its Stage-01a responsibility map.

    Empty when the map is absent (legacy / pre-01a), so callers fall back to
    the whole concept-source union. Feature-scoped per-UC artefacts (contracts,
    data models) must be produced only for these concepts — the union of
    concept-source dirs also contains every OTHER concept in the corpus."""
    resp = _resp_map(feature_root)
    if not os.path.isfile(resp):
        return []
    return [c for c in sorted(ap.parse_responsibility_map(resp)) if c != "Web"]


def feature_contract_concepts(feature_root: str) -> List[str]:
    """Concepts this feature must produce a concept contract for (delegates to
    `artifact_parsers`, the single source of truth shared with the 04b
    manifest)."""
    return ap.feature_contract_concepts(feature_root)


def feature_model_concepts(feature_root: str) -> List[str]:
    """Concepts this feature must produce a conceptual data model for.

    Delegates to `artifact_parsers.feature_model_concepts` (single source of
    truth, shared with the 03b file manifest) with this feature's resolved
    corpus dir."""
    return ap.feature_model_concepts(feature_root, _concept_corpus_dir(feature_root))


def _concept_dir_args(feature_root: str) -> List[str]:
    """`--concept-dir <d>` repeated once per concept-source dir, in precedence
    order. The consumer checks merge the dirs, earlier winning on a name clash."""
    args: List[str] = []
    for directory in concept_source_dirs(feature_root):
        args += ["--concept-dir", directory]
    return args


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

_SYNC_TRANSITION_COVERAGE = Check(
    name="sync_transition_coverage",
    script="verify_sync_transition_coverage.py",
    build_args=lambda r: ["--feature", r],
    requires=lambda r: [CHAIN_DIR(r), SYNC_DIR(r)],
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
    build_args=lambda r: ["--data-dir", DATA_DIR(r)] + _concept_dir_args(r),
    requires=lambda r: [DATA_DIR(r)] + _concept_source_requires(r),
)

_CONTRACT_PARITY = Check(
    name="contract_parity",
    script="verify_contract_parity.py",
    build_args=lambda r: _concept_dir_args(r) + ["--contract-dir", _contract_dir(r)],
    requires=lambda r: concept_source_dirs(r) + [_contract_dir(r)],
)

_OUTCOME_ALIGNMENT = Check(
    name="outcome_alignment",
    script="verify_outcome_alignment.py",
    build_args=lambda r: [
        "--chain-dir", CHAIN_DIR(r),
        # Feature contracts first, then the canonical corpus: a reused concept
        # has no feature-local contract and is validated against the canonical.
        "--contract-dir", _contract_dir(r),
        *[arg for d in concept_source_dirs(r)
          for arg in ("--contract-dir", d)],
    ],
    requires=lambda r: [CHAIN_DIR(r), _contract_dir(r), *concept_source_dirs(r)],
)

_ACTION_CHAIN = Check(
    name="action_chain",
    script="verify_action_chain.py",
    build_args=lambda r: [
        "--resp-map", _resp_map(r),
        "--chain-dir", CHAIN_DIR(r),
        *_concept_dir_args(r),
        "--sync-dir", SYNC_DIR(r),
        "--dep-dir", DEP_DIR(r),
        # The feature's own contracts first, then the canonical corpus: a reused
        # concept has no feature-local contract and binds the canonical one.
        "--contract-dir", _contract_dir(r),
        *[arg for d in concept_source_dirs(r)
          for arg in ("--contract-dir", d)],
    ],
    requires=lambda r: [
        _resp_map(r), CHAIN_DIR(r), *concept_source_dirs(r), SYNC_DIR(r),
        DEP_DIR(r), _contract_dir(r),
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

def _package_layout(feature_root: str) -> str:
    return os.path.join(feature_root, "_config", "package-and-layout.md")

_FEATURE_IMPL_PATHS = Check(
    name="profile_paths",
    script="verify_profile_paths.py",
    build_args=lambda r: ["--feature", r],
    requires=lambda r: [_package_layout(r)],
)

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
    # Scope to this feature's sync specs. Using --features-dir here would
    # demand that every other feature's syncs have an implementation in this
    # feature's impl dir (cross-feature false failures).
    build_args=lambda r: [
        "--sync-impl-dir", _sync_impl_dir(r),
        "--sync-dir", SYNC_DIR(r),
        "--strict-trigger",
    ],
    requires=lambda r: [_sync_impl_dir(r), SYNC_DIR(r)],
)

_FIELD_ASSERTIONS = Check(
    name="concept_field_assertions",
    script="verify_concept_field_assertions.py",
    build_args=lambda r: [
        # The tests under the test root include reused concepts' tests, so this
        # gate must see the canonical contracts too (R22).
        "--contract-dir", _contract_dir(r),
        *[arg for d in concept_source_dirs(r)
          for arg in ("--contract-dir", d)],
        "--test-source-root", _test_source_root(r),
    ],
    requires=lambda r: [_contract_dir(r), _test_source_root(r)],
)

def _mutation_configured(feature_root: str) -> bool:
    """True when the profile declares a mutation command (clad.properties
    `mutation.command`). Mutation gating is opt-in per profile."""
    return bool(_prop(feature_root, "mutation.command"))


def _mutation_requires(feature_root: str, rel: str) -> List[str]:
    """`requires` for the mutation-score check: a sentinel skips it when the
    profile has no mutation command or no configured test root."""
    out = output_dir(feature_root, rel)
    if not _mutation_configured(feature_root):
        return [os.path.join(out, "__no_mutation_command__")]
    if not _test_source_root(feature_root):
        return [os.path.join(out, "__no_test_source_root__")]
    return [out]


def _mutation_args(feature_root: str, scope: str) -> List[str]:
    """Args for the mutation-score check. `mutation.require=true` makes a SKIP
    (the tool cannot run in this environment) a failure — for CI."""
    args = ["--feature-root", feature_root, "--scope", scope]
    if (_prop(feature_root, "mutation.require") or "").strip().lower() in (
            "true", "1", "yes"):
        args.append("--require")
    return args


# Mutation score is the test-effectiveness gate (DR-0001). It runs the
# profile's mutation tool, which is slow, so it is skipped in the fast
# artefact gate and enforced by `advance` / the local pre-commit gate.
_MUTATION_SCORE_04D = Check(
    name="mutation_score",
    script="verify_mutation_score.py",
    build_args=lambda r: _mutation_args(r, "concepts"),
    requires=lambda r: _mutation_requires(r, "04_implement/04d_concept-impl"),
    skip_in_artefact_gate=True,
)

_MUTATION_SCORE_04E = Check(
    name="mutation_score",
    script="verify_mutation_score.py",
    build_args=lambda r: _mutation_args(r, "syncs"),
    requires=lambda r: _mutation_requires(r, "04_implement/04e_sync-impl"),
    skip_in_artefact_gate=True,
)

# The Acceptance Spec is the human-facing, frozen Gate-3 artifact (DR-0001).
# The binding check proves every spec row maps to a native test method and
# every scenario is covered; the gate content-hash in verify_stage_sequence.py
# provides the freeze (a changed spec stales Gate 3 and must be re-approved).
_ACCEPTANCE_BINDING = Check(
    name="acceptance_binding",
    script="verify_acceptance_binding.py",
    build_args=lambda r: [
        "--spec", os.path.join(
            output_dir(r, "04_implement/04c_acceptance-tests"),
            "acceptance-spec.md"),
        "--usecase", _usecase(r),
        "--chain-dir", CHAIN_DIR(r),
        "--test-source-root", _test_source_root(r),
    ],
    requires=lambda r: [
        os.path.join(output_dir(r, "04_implement/04c_acceptance-tests"),
                     "acceptance-spec.md"),
        _usecase(r),
    ],
)

_SYNC_DECLARATIVE = Check(
    name="sync_declarative",
    script="verify_sync_declarative.py",
    build_args=lambda r: [
        "--sync-impl-dir", _sync_impl_dir(r),
    ],
    requires=lambda r: [_sync_impl_dir(r)],
)

_ACTION_LOG_ISOLATION = Check(
    name="action_log_isolation",
    script="verify_action_log_isolation.py",
    build_args=lambda r: [
        "--app-source-root", os.path.dirname(_concept_impl_dir(r)),
    ] if _concept_impl_dir(r) else [],
    requires=lambda r: [_concept_impl_dir(r)],
)

_SYNC_CYCLE_GRAPH = Check(
    name="sync_cycle_graph",
    script="verify_sync_cycle_graph.py",
    build_args=lambda r: ["--sync-dir", SYNC_DIR(r)],
    requires=lambda r: [SYNC_DIR(r)],
)

_SYNC_OVERLAP = Check(
    name="sync_overlap",
    script="verify_sync_overlap.py",
    # Canonical fire-after-commit dispatch is single-threaded (one FactStore,
    # one engine queue) so concurrent lock-order deadlock is not reachable in
    # the runtime; the check stays on as a design-time advisory (contract
    # evidence: conduit rebuild experiment, maintenance/fire-after-commit
    # engine record). Revisit only when a multi-threaded dispatch profile
    # lands.
    build_args=lambda r: ["--sync-dir", SYNC_DIR(r), "--advisory"],
    requires=lambda r: [SYNC_DIR(r)],
)

def _expected_outputs(feature_root: str, key: str) -> List[str]:
    try:
        return ap.expected_stage_outputs(feature_root).get(key, [])
    except Exception:  # noqa: BLE001 - never let a parse error crash the gate
        return []


def _manifest_check(name: str, rel: str, key: str) -> Check:
    """A file-manifest check whose expected list is derived from the feature's
    approved upstream artefacts (see artifact_parsers.expected_stage_outputs)."""
    def _present(r: str) -> bool:
        return bool(_expected_outputs(r, key))

    return Check(
        name=name + "_file_manifest",
        script="verify_file_manifest.py",
        build_args=lambda r: [
            "--dir", output_dir(r, rel),
            "--expected", ",".join(_expected_outputs(r, key)),
        ],
        requires=lambda r: (
            [output_dir(r, rel)] if _present(r)
            else [os.path.join(output_dir(r, rel), "__no_expected_outputs__")]
        ),
    )


def _port_spec(feature_root: str) -> str:
    return os.path.join(
        os.path.dirname(feature_root), "_system", "stages", "00_actor-goal",
        "output", "port-spec.md")


def _adapter_surface_present(feature_root: str) -> bool:
    """True when the feature crosses an adapter surface.

    HTTP today: a `port-spec.md` inbound entry, a `Web` bootstrap in any chain
    table, or `Web` in the use case. Used to make the adapter-test check skip
    cleanly for non-adapter features/profiles instead of reporting a false green.
    """
    spec = _port_spec(feature_root)
    if os.path.isfile(spec):
        try:
            with open(spec, encoding="utf-8", errors="replace") as fh:
                if re.search(r"\binbound\b", fh.read(), re.IGNORECASE):
                    return True
        except OSError:
            pass
    chain_dir = CHAIN_DIR(feature_root)
    if os.path.isdir(chain_dir):
        for name in sorted(os.listdir(chain_dir)):
            if not name.endswith("-chain.md") or name.endswith("-all-scenarios-chain.md"):
                continue
            try:
                with open(os.path.join(chain_dir, name), encoding="utf-8",
                          errors="replace") as fh:
                    if re.search(r"Web[/.](?:request|handle|respond)", fh.read()):
                        return True
            except OSError:
                continue
    usecase = _usecase(feature_root)
    if os.path.isfile(usecase):
        try:
            with open(usecase, encoding="utf-8", errors="replace") as fh:
                return bool(re.search(r"\bWeb\b", fh.read()))
        except OSError:
            return False
    return False


def _adapter_test_requires(feature_root: str, stage_rel: str) -> List[str]:
    """`requires` for the adapter-test check: a sentinel skips it when the
    feature has no adapter surface or no configured test root."""
    out = output_dir(feature_root, stage_rel)
    if not _adapter_surface_present(feature_root):
        return [os.path.join(out, "__no_adapter_surface__")]
    if not _test_source_root(feature_root):
        return [os.path.join(out, "__no_test_source_root__")]
    return [out]


_CHAIN_MANIFEST = _manifest_check("chain", "01b_chain-table", "01b")
_CONCEPT_MANIFEST = _manifest_check("concept", "02_concepts", "02")
_CARD_MANIFEST = _manifest_check("dependency", "03a_dependency-review", "03a")
_DATA_MODEL_MANIFEST = _manifest_check("data_model", "03b_data-model", "03b")
_CONTRACT_MANIFEST = _manifest_check("contract", "04_implement/04b_contract", "04b")
_ACCEPTANCE_MANIFEST = _manifest_check(
    "acceptance", "04_implement/04c_acceptance-tests", "04c")
_CONCEPT_IMPL_MANIFEST = _manifest_check(
    "concept_impl", "04_implement/04d_concept-impl", "04d")
_SYNC_IMPL_MANIFEST = _manifest_check(
    "sync_impl", "04_implement/04e_sync-impl", "04e")

_PORT_SPEC_04B = Check(
    name="port_spec_contract",
    script="verify_port_spec_contract.py",
    build_args=lambda r: [
        "--port-spec", _port_spec(r),
        "--contract-dir", _contract_dir(r),
    ],
    requires=lambda r: [_port_spec(r), _contract_dir(r)],
)

_PORT_SPEC_04C = Check(
    name="port_spec_contract",
    script="verify_port_spec_contract.py",
    build_args=lambda r: [
        "--port-spec", _port_spec(r),
        "--contract-dir", _contract_dir(r),
        "--feature-dir", output_dir(r, "04_implement/04c_acceptance-tests"),
    ],
    requires=lambda r: [_port_spec(r), _contract_dir(r)],
)

_ADAPTER_TEST_04C = Check(
    name="adapter_test",
    script="verify_adapter_test.py",
    build_args=lambda r: [
        "--feature-root", r,
        "--test-source-root", _test_source_root(r) or "",
    ],
    requires=lambda r: _adapter_test_requires(r, "04_implement/04c_acceptance-tests"),
)

_ADAPTER_TEST_05 = Check(
    name="adapter_test",
    script="verify_adapter_test.py",
    build_args=lambda r: [
        "--feature-root", r,
        "--test-source-root", _test_source_root(r) or "",
        "--require-enabled",
    ],
    requires=lambda r: _adapter_test_requires(r, "05_verify"),
)

_CLOSE_EVIDENCE = Check(
    name="close_evidence",
    script="verify_close_evidence.py",
    build_args=lambda r: [
        "--feature-root", r,
        "--test-source-root", _test_source_root(r),
    ],
    requires=lambda r: [output_dir(r, "05_verify")],
)

_COLLECTION_COVERAGE = Check(
    name="collection_coverage",
    script="verify_collection_coverage.py",
    build_args=lambda r: ["--feature", r],
    requires=lambda r: [
        CHAIN_DIR(r),
        output_dir(r, "04_implement/04c_acceptance-tests"),
    ],
)

_CONCEPT_TEST_DERIVATION = Check(
    name="concept_test_derivation",
    script="verify_concept_test_derivation.py",
    build_args=lambda r: [
        "--contract-dir", _contract_dir(r),
        "--derivation", os.path.join(
            output_dir(r, "04_implement/04d_concept-impl"),
            "concept-test-derivation.md"),
        "--test-source-root", _test_source_root(r),
    ],
    requires=lambda r: [
        _contract_dir(r),
        os.path.join(output_dir(r, "04_implement/04d_concept-impl"),
                     "concept-test-derivation.md"),
        _test_source_root(r),
    ],
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
        "--dir", output_dir(r, "01a_responsibility-map"),
        "--expected", "responsibility-map.md",
    ],
    requires=lambda r: [output_dir(r, "01a_responsibility-map")],
)

_CHAIN_GRAMMAR = Check(
    name="chain_grammar",
    script="verify_chain_grammar.py",
    build_args=lambda r: ["--chain-dir", CHAIN_DIR(r)],
    requires=lambda r: [CHAIN_DIR(r)],
)

_DISTINCT_OUTCOMES = Check(
    name="distinct_outcomes",
    script="verify_distinct_outcomes.py",
    build_args=lambda r: ["--chain-dir", CHAIN_DIR(r)],
    requires=lambda r: [CHAIN_DIR(r)],
)

_OUTCOME_CASING = Check(
    name="outcome_casing",
    script="verify_outcome_casing.py",
    build_args=lambda r: ["--feature", r],
    requires=lambda r: [CHAIN_DIR(r)],
)


_CONCEPT_STATE_RELATIONAL = Check(
    name="concept_state_relational",
    script="verify_concept_state_relational.py",
    build_args=lambda r: _concept_dir_args(r),
    requires=lambda r: _concept_source_requires(r),
)

_CONCEPT_CRITERIA = Check(
    name="concept_criteria",
    script="verify_concept_criteria.py",
    build_args=lambda r: _concept_dir_args(r),
    requires=lambda r: _concept_source_requires(r),
)

_CONCEPT_PROPOSALS = Check(
    name="concept_proposals",
    script="verify_concept_proposals.py",
    build_args=lambda r: ["--feature", r],
    requires=lambda r: [_resp_map(r), output_dir(r, "02_concepts")],
)

_CONCEPT_ADDITIVITY = Check(
    name="concept_additivity",
    script="verify_concept_additivity.py",
    build_args=lambda r: ["--feature", r],
    requires=lambda r: [_resp_map(r)] + _concept_source_requires(r),
)

_REUSED_CONTRACTS = Check(
    name="reused_concept_contracts",
    script="verify_reused_concept_contracts.py",
    build_args=lambda r: ["--feature", r],
    requires=lambda r: [_resp_map(r)],
)


_RELATIONAL_MAPPING = Check(
    name="relational_mapping",
    script="verify_relational_mapping.py",
    build_args=lambda r: ["--storage-dir", output_dir(r, "04_implement/04a_storage-mapping")],
    requires=lambda r: [output_dir(r, "04_implement/04a_storage-mapping")],
)


# --------------------------------------------------------------------------
# The canonical per-UC stage order.
# --------------------------------------------------------------------------

STAGES: List[Stage] = [
    Stage("01", "Use case", "01_usecase",
          checks=[_FILE_01]),
    Stage("01a", "Responsibility map", "01a_responsibility-map",
          checks=[_FILE_02A]),
        Stage("01b", "Chain table", "01b_chain-table", gate_after=1,
            # `distinct_outcomes` (D3): a single completion token must not fan
            # out to two terminal responses. `outcome_casing` (D9/D26): authored
            # outcome tokens are SCREAMING_SNAKE_CASE, here and in Stage 02.
            checks=[_CHAIN_GRAMMAR, _DISTINCT_OUTCOMES, _OUTCOME_CASING,
                    _CHAIN_MANIFEST]),
        Stage("02", "Concept specs", "02_concepts",
          # `concept_additivity` runs here, at the stage that AUTHORS an extend;
          # waiting until 03b/04b let a non-additive extension be written first
          # (experiment defect D38). It skips for `new` concepts (no canonical).
          checks=[_CONCEPT_STATE_RELATIONAL, _CONCEPT_CRITERIA,
                  _CONCEPT_PROPOSALS, _CONCEPT_ADDITIVITY, _OUTCOME_CASING,
                  _CONCEPT_MANIFEST]),
    Stage("03", "Syncs", "03_syncs", checks=[_SCENARIO_COVERAGE, _SYNC_MATRIX,
          _SYNC_TRANSITION_COVERAGE,
          _SYNC_CYCLE_GRAPH, _SYNC_OVERLAP]),
    Stage("03a", "Dependency review", "03a_dependency-review",
          checks=[_CARD_MANIFEST]),
    Stage("03b", "Data model", "03b_data-model", gate_after=2,
          checks=[_DATA_MODEL, _DATA_MODEL_MANIFEST, _CONCEPT_ADDITIVITY]),
    Stage("04a", "Storage mapping", "04_implement/04a_storage-mapping",
          # profile_paths runs here as well as at 04c: the guard's own advice is
          # "fill `_config` at Stage 04a before advancing", and until it was
          # wired here `advance` happily passed 04a with a TBD layout, so the
          # checks then audited the seed's tree instead of the app's.
          checks=[_RELATIONAL_MAPPING, _FEATURE_IMPL_PATHS]),
    Stage("04b", "Concept contract", "04_implement/04b_contract",
          checks=[_CONTRACT_PARITY, _OUTCOME_ALIGNMENT, _ACTION_CHAIN,
                  _CONTRACT_MANIFEST, _CONCEPT_ADDITIVITY, _REUSED_CONTRACTS,
                  _PORT_SPEC_04B]),
    Stage("04c", "Acceptance tests", "04_implement/04c_acceptance-tests",
          gate_after=3,
          checks=[_FEATURE_IMPL_PATHS, _ACCEPTANCE_BINDING, _COLLECTION_COVERAGE,
                  _ADAPTER_TEST_04C, _PORT_SPEC_04C, _ACCEPTANCE_MANIFEST]),
    Stage("04d", "Concept implementation", "04_implement/04d_concept-impl",
          checks=[_FEATURE_IMPL_PATHS, _CONCEPT_TEST_DERIVATION, _FIELD_ASSERTIONS,
                  _MUTATION_SCORE_04D, _CONCEPT_IMPL_MANIFEST]),
    Stage("04e", "Sync implementation", "04_implement/04e_sync-impl",
          checks=[_FEATURE_IMPL_PATHS, _IMPL_PARITY, _SYNC_IMPL_PARITY,
                  _SYNC_ROUTE_FILTERS, _SYNC_DECLARATIVE, _ACTION_LOG_ISOLATION,
                  _MUTATION_SCORE_04E, _SYNC_IMPL_MANIFEST]),
    Stage("05", "Verify", "05_verify",
          checks=[_CLOSE_EVIDENCE, _ADAPTER_TEST_05]),
]

GATE_LABELS = {
    1: "Requirements",
    2: "Architecture",
    3: "Acceptance spec",
}

# Stages whose output a given human gate approves. A gate approval is bound to
# the content hash of these stages: if any of them is re-derived after approval,
# the approval is stale and the gate must be re-presented. Single source of
# truth — present_gate.py and the gate checks derive from this, not from their
# own copies.
GATE_STAGES = {
    1: ["01", "01a", "01b"],
    2: ["02", "03", "03a", "03b"],
    3: ["04a", "04b", "04c"],
}


def gate_stages(gate_num: int) -> List[str]:
    """Return the canonical stage ids approved by a human gate."""
    return list(GATE_STAGES.get(gate_num, []))


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


_PROPERTY_KEY_MD = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.[A-Za-z0-9_.-]+$")


def _config_value_from_file(path: str) -> str:
    """Value body of a feature-local `<key>.md` override file.

    The value is the first non-comment, non-blank line, trimmed. A comment is
    an HTML comment (`<!-- ... -->`) or a line starting with `#`. An empty
    (or comment-only) file yields '' — meaning "override not set".
    """
    try:
        with open(path) as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("<!--") or stripped.endswith("-->"):
                    continue
                return stripped
    except OSError:
        pass
    return ""


def _read_config(feature_root: str) -> Dict[str, str]:
    """Read effective configuration as a flat dict of key -> value.

    Sources, in the documented resolution order (AGENTS.md §4a, lower
    number wins):

    1. Feature-local override — `<feature_root>/_config/<key>.md`, one file
       per key, whose body is the value. Only files whose stem looks like a
       dotted property key (`test.source.root.md`, not `README.md`) are
       considered, so feature-reference docs never become phantom keys.
    2. Repo-root `clad.properties` (INI-free key=value format).
    """
    root_path = os.path.join(_repo_root(feature_root), "clad.properties")
    result: Dict[str, str] = {}
    if os.path.exists(root_path):
        with open(root_path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                key = k.strip()
                # Strip inline comments from values (e.g. 'value  # comment')
                value = v.strip()
                if "  #" in value:
                    value = value.split("  #")[0].rstrip()
                result[key] = value
    config_dir = os.path.join(feature_root, "_config")
    if os.path.isdir(config_dir):
        for name in sorted(os.listdir(config_dir)):
            if not name.endswith(".md") or not _PROPERTY_KEY_MD.match(
                    name[:-len(".md")]):
                continue
            value = _config_value_from_file(os.path.join(config_dir, name))
            if value:
                result[name[:-len(".md")]] = value
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


def get_property(feature_root: str, key: str) -> str | None:
    """Public API — read a single property from clad.properties.
    Returns None if the file or key is not found. Walks up from
    feature_root to find clad.properties, then reads the value."""
    cfg = _read_config(feature_root)
    value = cfg.get(key)
    return value if value else None
