# Artefact impact matrix — `transport-framing-adapter-owned`

> Iterative change to the UC-00-login worked example, presentation only: four
> respond sync specs stop writing the transport frame (`body: { … }`) and pass
> the **authored result** flat. Response framing is the primary adapter's
> serialization step (`methodology/overlays/PORTS_AND_ADAPTERS.md`;
> `maintenance/transport-framing-adapter-owned.md`).

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `03`
- **Status:** `closed`
- **Change summary:** `RespondWhenCheckBadPassword`, `RespondWhenCheckLocked`,
  `RespondWhenGrantGranted`, and `RespondWhenLookupByUsernameRefused` drop the
  `body: { … }` wrapper from their `then` signature (matrix cell and rule
  block). Statuses, payload fields, outcomes, and observable behaviour are
  unchanged.

| Artefact | Touched? | How |
|---|---|---|
| Use case | no | — |
| Concept(s) | no | — |
| Sync(s) | yes | 4 specs: `then` signature de-framed (2 lines each) |
| Contract slices | no | — |
| Flow tests | no | they assert the adapter's framed output, unchanged |
| Concept tests | no | — |
| Sync tests | no | — |
| Production code | no | `LoginSyncs` already passes the fields flat |
| Verification trace | no | — |

## Re-derivation order

1. `03` sync outputs — 4 specs de-framed.
2. Re-present and re-approve **Gate 2** (03 is in its block).

## Notes

- This resolves a latent spec/implementation divergence: the specs promised
  `body: { sessionToken: ?sid }` while `LoginSyncs` passed `sessionToken`
  flat, and no check compared `then` argument shape
  (`verify_sync_implementation_parity` matches targets only). The specs now
  agree with the implementation.
- Gate approval is content-hash bound: 03 changed, so Gate 2 must be
  re-approved. Gate 1 and Gate 3 are unaffected.
- Do not hand-edit the RESUME `## Gate snapshot` hashes —
  `approve_gate.py` owns them.
