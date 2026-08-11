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
| Production code | `yes` | SplitStorage (new), CladDatasetFactory (refactored), README (docs) |

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
