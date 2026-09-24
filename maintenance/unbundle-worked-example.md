# Maintenance change — `unbundle-worked-example`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** workspace layout (`features/` → `examples/`), the system-scope concept corpus, `reference-impl/` reactor, docs, gate tests
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Move the worked example out of the live project workspace. `features/UC-00-login/` → `examples/UC-00-login/`; the pedagogical `reference-impl/java-plain/` → `examples/java-plain/` (standalone build). The system-scope concept corpus starts **empty** — a project's domain is unknown up front. Stage contracts gain a one-line pointer to the completed example, so the reference stays available per stage without duplicating artefacts.

## Why

A clone carries UC-00-login (a frozen login feature) and its reference
implementation into every project. Several projects do not need it, and it
causes confusion: the concept corpus is seeded with login concepts a project
never asked for, `reference-impl/` ships a demo module, and every doc must warn
"do not copy `features/UC-00-login/`". The example is **teaching material**, not
live workspace; `features/` should hold only the project's own use cases.

The tooling already treats `UC-00-*` as special (the registry,
shared-action-contracts, corpus-current, manifest, and transition-coverage
checks exclude the prefix). After the move, `examples/` is simply **not a
feature root** — the exclusions become location-based, which is simpler.

## Rule

- **Relocate the example.** `features/UC-00-login/` → `examples/UC-00-login/`
  (frozen; its Stage-02 output stays as-is, no second corpus is created).
- **Relocate the pedagogical profile.** `reference-impl/java-plain/` →
  `examples/java-plain/`, built **standalone** (its own pom, depending on the
  installed `legible-engine`); removed from the `reference-impl` reactor. The
  engine demo features (`social`/`tagging`/`token`) and the login realisation
  that `legible-storage`'s contract test uses stay in
  `reference-impl/java-legible/`, reframed as the engine's test/demo profile.
- **Empty the corpus.** Remove `features/_system/concepts/*` and the
  login-seeded `concepts-catalog.md` / `concept-dependence.md` content; leave
  empty scaffolds (with a header note) so the corpus gates stay wired. A
  project's corpus starts empty and grows only from its own features.
- **Repoint coupling.** `legible-storage`'s `LoginSchemas` javadoc and
  `RmapDeriverTest` read the example's Stage-02 specs by path → new path; the
  gate tests that read `features/UC-00-login` → `examples/UC-00-login`.
- **Per-stage pointers.** Each skeleton stage `CONTEXT.md` (and the example's
  own contracts) gains one line: "A completed example of this stage:
  `examples/UC-00-login/stages/NN_.../output/`." No artefact duplication.
- **Docs.** Repoint `AGENTS.md`, `CONTEXT.md`, `README.md`, `CONTRIBUTING.md`,
  `methodology/` (README, WALKTHROUGH, ARTEFACT_MAP, GHERKIN_INTEGRATION), and
  `ROADMAP.md`.

## Mechanism

The change is structural (moves + corpus reset), so the load-bearing mechanism
is the corpus resolver the gates read: `clad_stages._concept_corpus_dir`
(quality-gate/clad_stages.py:102) resolves the corpus through the `concepts.dir`
property, defaulting to `features/_system/concepts`, and returns `''` when the
directory is absent; `concept_source_dirs` (quality-gate/clad_stages.py:117)
then falls back to the feature's own Stage-02 output. With the corpus emptied
(the directory kept, `.gitkeep`), every corpus check reports 0 concepts rather
than skipping. `legible-storage`'s `RmapDeriverTest` reads the example specs by
path (reference-impl/legible-storage/src/test/java/dev/legible/storage/RmapDeriverTest.java:24),
repointed to `examples/UC-00-login/…`.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Layout/tooling change; example artefacts unchanged |
| Action ordering and sync deduplication | `preserved` | Engine unchanged |
| Flow-token lineage | `preserved` | Engine unchanged |
| Storage/retention semantics | `preserved` | Engine + storage unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | README, AGENTS, CONTEXT, methodology docs, stage contracts |
| Profile configuration or deployment files | yes | `examples/java-plain/pom.xml` (standalone); reactor `pom.xml` (drop module) |
| Engine/runtime implementation | no | — |
| Profile tests | yes | `RmapDeriverTest` path; `java-plain` standalone build |
| Gate scripts/tests | yes | the `UC-00`-prefix tests repoint to `examples/`; corpus checks start empty |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Example artefacts intact (no content change) | integration | `git status --short`/`--stat`: `R` renames for the example stages; only the README + Stage-00 location notes changed | pass | — |
| Corpus empty + gates green | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs; `concept_registry`: 0 concepts, `shared_triggers`: empty view |
| Gate suite green (tests repointed) | unit | `python3 -m pytest quality-gate/tests -q` | pass | 254 passed |
| Reactor builds without java-plain | integration | `mvn test -f reference-impl/pom.xml` | pass | BUILD SUCCESS (engine, legible, bench, storage, micronaut) |
| Example builds standalone | integration | `mvn -f examples/java-plain/pom.xml test` (after `mvn install -pl legible-engine -am -DskipTests`) | pass | 19 tests, BUILD SUCCESS |
| Doc links resolve | integration | `verify_links.py` (313 links) + repo-wide scan incl. CI-covered files | pass | 0 dead links |

## Gates

### Design gate

To be approved before implementation. Approve with
`./clad approve-maintenance unbundle-worked-example design`.

### Evidence gate

Cleared: the example moved intact (git renames; the Stage-00 outputs travel with it as `examples/UC-00-login/system-stage-00/`); the corpus is empty with constructs scaffolds and every corpus gate reports a clean 0; the reactor builds without java-plain and the example builds standalone (19 tests); 254 gate tests green; artefact pipeline intact (0 WARNs); zero dead links repo-wide.

## Notes

- **Blast radius:** a feature-folder move plus a reactor change plus ~30 doc/test
  pointers. It changes the starter's directory contract, so it lands as its own
  change (candidate `0.13.0`).
- **Reversibility:** layout only; `git mv` back restores the prior shape.
