# Maintenance change — engine runtime docs + stale-framing fixes

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all (docs); legible-engine (comment only)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** document the fire-after-commit runtime — how sync chains
  are constructed and displayed, and what `stuck` means now that nothing polls —
  in `ENGINE.md`, and correct stale Jena/SPARQL/poll framing in a few docs and
  one engine javadoc. No behavioural change.

## Mechanism

`methodology/architecture/ENGINE.md` gains four sections: "The action log —
invocations and completions" (the `Invocation`/`Completion` records and the
`parentActionId`/`causedBySync` provenance edges), "Sync dispatch — from a
completion to the next invocation" (the trigger index, conjunct matching,
provenance-based exactly-once, and the synchronous pending-queue drain),
"The debug surface — designed vs realized chains" (`/api/dev/syncs` vs
`/api/dev/flow/{id}`), and "Stuck, replay, and quiescence" (`stuck()` semantics
and `drain`/replay). Cross-links added from `SYNCHRONIZATIONS.md`,
`FLOW_TOKENS.md`, and `reference-impl/legible-engine/README.md`.

Stale framing corrected (comment/doc only): `SyncEngine.java#debug` javadoc
(was "the Jena profile's `/api/dev/*` endpoints"); `QUALITY_GATE.md` ("ships
with this starter" still named Jena); `SYNC_ENGINE_EVOLUTION.md` (the current
`FactStore` SPI listed Jena); `overlays/DECISIONS.md` (the example prompt "why
Jena over Postgres" predated Jena's retirement). Verified against the code:
`SyncEngine#run`/`#drain`/`#processInvocation` and `DebugApi#stuck`/`#syncs`/
`#flow` (`reference-impl/legible-engine/src/main/java/dev/legible/engine/`).

## Contract impact

| Surface | Impact |
|---|---|
| Action outcomes / response contracts | preserved |
| Action ordering / sync dedup | preserved |
| Flow-token lineage | preserved (docs now describe it) |
| Storage / retention semantics | preserved |
| Gate verdicts | preserved |

## Impact matrix

| Artefact | Changed? | What |
|---|---|---|
| Documentation | yes | `ENGINE.md`, `SYNCHRONIZATIONS.md`, `FLOW_TOKENS.md`, `QUALITY_GATE.md`, `SYNC_ENGINE_EVOLUTION.md`, `DECISIONS.md`, engine README |
| Profile config / deployment | no | — |
| Engine / runtime impl | comment only | `SyncEngine.java#debug` javadoc (no behaviour) |
| Profile tests | no | — |
| UC artefact chain | no | — |

## Test matrix

| Invariant | Level | Command | Status | Evidence |
|---|---|---|---|---|
| Doc links resolve | gate | `python3 quality-gate/verify_artefacts.py` | pass | `doc_links` |
| No retired sync grammar reintroduced | unit | `python3 -m pytest quality-gate/tests -q` | pass | `test_no_stale_sync_grammar` |
| Engine still compiles | build | `mvn -q -f reference-impl/pom.xml -pl legible-engine -am test-compile` | pass | comment-only change |

## Gates

### Design gate

Approved by the operator in-session: extend `ENGINE.md`; include the engine
javadoc fix with a maintenance record; patch release.

### Evidence gate

Approved on the green artefact pipeline and quality-gate suite; no behavioural
change to verify.

## Notes

- Docs-only plus one javadoc comment; no re-entry to any feature artefact chain.
- Agents must not create/push the `v0.15.1` tag; the human does (AGENTS §2.16).
