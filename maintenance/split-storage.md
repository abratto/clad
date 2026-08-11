# split-storage — in-memory action log + remote Fuseki business graphs

- **Change category:** `structural`
- **Why:** Unbounded TDB2 growth from action log DELETEs — TDB2 creates
  tombstones that never free physical space. The action log is transient
  execution state, not durable data. Moving it to in-memory Jena bounds
  RAM usage, reclaims memory on DELETE, and eliminates the need for
  periodic `tdb2.tdbcompact`.

## Impact

| Artefact | Touched? | How |
|---|---|---|
| Concept(s) | `no` | |
| Sync(s) | `no` | |
| SPEC slices | `no` | |
| Flow tests | `no` | |
| Concept tests | `no` | |
| Sync tests | `no` | |
| Production code | `yes` | SplitStorage, FlowArchiver, FlowArchiveBuffer, FlowArchiveException (new); CladDatasetFactory (refactored); DebugController (updated); README + clad.properties (docs) |

## Technical change

- **SplitStorage** routes SPARQL operations by graph IRI. Action log
  graphs (`GRAPH <actions>`, `GRAPH <actions/archive>`) → in-memory
  Jena TxnMem. Business graphs → remote Fuseki. Batch operations
  (beginBatch/flushBatch) run against the action log backend.
- **CladDatasetFactory** refactored: `fusekiStorage()`,
  `fusekiSplitStorage()`, `buildRemote()` helper.
- **New backend:** `engine.dataset.type=fuseki-split`. Uses same
  endpoint/credential env vars as `fuseki`.

## Runtime invariants

1. Sync WHERE clauses read from the action log graph — must be served
   by the in-memory backend. Verified: `SplitStorage.forSparql()` routes
   `ACTION_GRAPH_IRI` and `ACTION_ARCHIVE_GRAPH_IRI` to in-memory.
2. Business writes (concept graph INSERTs) must route to remote Fuseki.
   Verified: `forSparql()` sends non-action-log SPARQL to businessBackend.
3. All existing tests pass. Verified: `mvn test -Dtest=PredicateEngineTest`.

## Transaction note

Action log and business graphs are NOT in the same transaction under
the split backend. This matches the existing logical separation:
concepts write business state in `processInvocation()`, then write
the action log completion in `writeCompletion()`. The two writes were
never in the same atomic boundary — even with a single backend, there
was a method-call window between them.

## FlowArchiver — log flush before delete

`FlowArchiver` serializes completed flow triples as N-Quads-in-JSON
log entries before they are deleted from the in-memory action log.
Configurable via `engine.archive.log.enabled=true`.

**Flush-before-delete guarantee:** `FlowArchiver.archiveFlow()` throws
`FlowArchiveException` on failure. `SplitStorage.archiveFlow()` calls
the archiver first — if it throws, the delete is skipped. Triples
remain in the in-memory action log for retry.

## FlowArchiveBuffer — debug endpoint fallback

When `engine.archive.flows=false`, completed flow triples are deleted
from the action log. `FlowArchiveBuffer` stores the last N completed
flows (default 100, configurable via `engine.archive.buffer.size`)
in an LRU-evicting in-memory map. `DebugController.flow()` checks the
buffer when the action log SELECT returns empty.

**Thread safety:** synchronized blocks on the internal `LinkedHashMap`.
Writes happen on the dispatch thread; reads on the HTTP handler thread.

## Configuration summary

```properties
# clad.properties (all now defaults)
engine.dataset.type=fuseki-split      # in-memory action log + remote Fuseki
engine.archive.flows=false            # no archive graph growth
engine.archive.log.enabled=false      # N-Quads JSON log archival (opt-in)
engine.archive.buffer.size=100        # debug buffer entries (0 to disable)
```

All properties resolve from env vars (`CLAD_*`) for containerized deployments.
