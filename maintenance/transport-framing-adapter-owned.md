# Maintenance change — `transport-framing-adapter-owned`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (methodology + templates + gate + the UC-00 worked example)
- **Feature-contract impact:** `re-entered`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Sync `then` arguments are the **authored result**; the transport envelope (status, body nesting) is the **primary adapter's** serialization step. Nested-map syntax in a sync `then` is a boundary violation and is flattened out of the shipped specs.

## Why

`methodology/overlays/PORTS_AND_ADAPTERS.md` already assigns serialization to
the primary adapter: it may "invoke one authored bootstrap action / flow root;
await the authored result; and **serialize it to the transport's response**",
and must not choose a domain branch.

The sync specs nevertheless write the wire frame into coordination:

```
then { Web/respond: [ status: 200 ; body: { sessionToken: ?sid } ] }
```

`body: { … }` is pure response framing. Worse, it is **unenforceable and
already divergent**: the shipped `java-legible` implementation passes
`sessionToken` flat while its spec promises `body: { sessionToken }`, and
`verify_sync_implementation_parity` compares only the `then` *target*
(`then_matches`), never the argument shape — so nothing detects it.

Found by the library-lending experiment: the app had to invent envelope
nesting inside its bootstrap concept to satisfy tests written against the frame
the spec promised. The right fix is to stop promising the frame in a sync, not
to teach the DSL to reproduce it (which would entrench the leak).

## Rule

- A sync `then` passes the **authored result**: flat domain fields the exit
  action consumes.
- Response shape — `status`, and any `body`/envelope nesting — is the primary
  adapter's serialization (or the bootstrap concept's implementation as the
  transport exit).
- `status` is retained in `then` for now: it is the established, check-bound
  convention (01b chain tables, every respond spec). Owning the *outcome →
  status* mapping in the adapter is recorded as a separate future decision.
- A nested map in a `then` signature is a defect.

## Mechanism

`verify_sync_then_shape` refuses a nested-map `then` argument, keeping the
transport envelope in the adapter (`quality-gate/verify_sync_then_shape.py`).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Only the *frame* is removed from the spec; observed statuses, payload fields, and outcomes are unchanged |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | The DSL is deliberately unchanged |
| Gate scripts | yes | new `verify_sync_then_shape.py`, wired into `verify_artefacts.py`; starts as WARN, flips to FAIL once the shipped specs are flat |
| Gate tests | yes | fixtures for flat-accept / nested-warn |
| Methodology docs | yes | `SYNCHRONIZATIONS.md` §"then arguments"; `templates/sync.md` |
| UC-00 artefacts | yes | four respond specs flattened (03 output → Gate 2 re-approval) |
| UC-01 artefacts | yes | four respond specs flattened (03 output → Gate 2 re-approval) |
| UC-00 / UC-01 implementation | no | their Java already passes flat fields; no behaviour change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| A flat `then` passes | unit | `test_sync_then_shape.py::test_flat_then_passes` | pass | — |
| A nested `{ … }` in `then` is reported | unit | `test_sync_then_shape.py::test_nested_body_fails` | pass | names the file/line |
| Advisory mode warns instead of failing | unit | `test_sync_then_shape.py::test_nested_body_is_advisory_when_asked` | pass | — |
| UC-00 specs are flat after the change | integration | `verify_sync_then_shape.py --features-dir features` | pass | 7 sync specs, 0 findings |
| Pipeline + sequence intact | integration | `verify_artefacts.py`; `verify_stage_sequence --feature features/UC-00-login --through 05` | pass | intact; sequence intact |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 141 passed |
| Reactor intact | integration | `mvn -q test -f reference-impl/pom.xml -pl java-legible -am` | pass | exit 0 |

## Gates

### Design gate

Approved in-conversation: the transport frame is adapter-owned; syncs carry the
authored result; the DSL is not changed.

### Evidence gate

To be recorded after the specs are flattened and the guard flips to FAIL.

## Notes

- UC-00's Java already passes flat fields, so flattening its specs makes spec
  and implementation agree — no Java or test change, only a Gate 2 re-approval.
- UC-01's adapter (its bootstrap concept as transport exit) already produces the
  framed response its tests assert; flattening its specs does not change the
  tests.
- Not in scope: moving the *status* decision to the adapter (a larger
  convention change spanning chain tables and every respond spec).
