<!-- Maintenance-route planning record. -->
# Maintenance change — `canonical-profile-pointers`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/java-legible` (canonical), `reference-impl/java-micronaut-jena` (legacy)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Re-point agent-facing guidance (stage CONTEXT templates, clad.properties impl paths, AGENTS.md rule examples) from the legacy java-micronaut-jena profile to the canonical java-legible / fire-after-commit engine, while keeping the legacy profile documented as an explicitly-selected alternative.

## Why

`reference-impl/README.md` and `AGENTS.md` §9 already name the fire-after-commit
engine canonical (R10/R21 retired), but the surfaces an agent actually reads at
Stage 04/05 still steered to the legacy RDF/SPARQL profile: the 04c–05 stage
CONTEXT templates listed `java-micronaut-jena/{SYNC_LOWERING,CODE_STYLE,CANONICAL_EXEMPLAR}.md`
as Layer-3 inputs (SPARQL lowering patterns for the *retired* engine),
`clad.properties test.source.root` pointed at the Jena profile's test tree while
`sync.impl.dir`/`concept.impl.dir` pointed at java-legible, and the engine.*
settings block was presented as current config though `legible-engine` never
reads those keys. An agent following the templates verbatim could re-derive the
retired engine's patterns despite the canonical statement.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Documentation/pointer change only; no concept/sync/runtime surface touched. |
| Action ordering and sync deduplication | preserved | No engine change. |
| Flow-token lineage | preserved | No runtime change. |
| Storage/retention semantics | preserved | `engine.dataset.*` keys remain present (legacy profile), now labelled legacy. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `AGENTS.md` (R2 wording, R17 example paths); stage CONTEXT templates 04d router + 04d-red + 04d-green + 04e-red + 04e-green + 04 router + 05 verify + `_config/package-and-layout.md` |
| Profile configuration or deployment files | yes | `clad.properties` — `test.source.root` moved to `java-legible`; legacy engine-settings block labelled LEGACY; example comments updated |
| Engine/runtime implementation | no | — |
| Profile tests | no | — |
| UC artefact chain | no | Templates only; no UC artefact re-derivation |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Artefact pipeline gate intact after edits | gate | `python3 quality-gate/verify_artefacts.py` | pass | exit 0 |
| Quality-gate regression suite unaffected | unit | `python3 -m unittest discover -s quality-gate/tests` | pass | 45/45 |
| No unlabelled legacy references remain in templates | check | `grep -rn java-micronaut-jena templates/feature-skeleton/ \| grep -v legacy` | pass | only intentional "profile is legacy" prose remains |

## Gates

### Design gate

Approved — the change re-points documentation and configuration examples to the
already-canonical engine; no contract or runtime behaviour changes.

### Evidence gate

Approved — artefact gate + regression suite green after the edits.

## Notes

- The legacy profile (`clad-engine`, `java-micronaut-jena`,
  `java-micronaut-postgres`) remains in the repo "until the remaining profiles
  are re-lowered onto the fire-after-commit engine" (reference-impl README);
  templates now mark its docs as "legacy profile only — do NOT follow when
  targeting java-legible" instead of "only when this profile is selected",
  which never said which profile was the default.
- `clad.properties engine.*` keys are retained so the legacy profile remains
  runnable, but they are explicitly labelled as unread by `legible-engine`.
