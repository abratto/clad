# Machine-facing CLAD contract

CLAD artefacts remain Markdown because human review is part of the workflow.
Consumers such as `clad-agent` must not independently parse that Markdown when
CLAD can provide the same information through a deterministic descriptor.

## Feature descriptor

Run:

```text
python3 quality-gate/describe_feature.py --feature features/UC-XX-slug
```

The command emits JSON with this envelope:

```json
{
  "contract": {
    "name": "clad.feature-descriptor",
    "version": 1,
    "capabilities": [
      "concepts.v1", "scenarios.v1", "syncs.v1",
      "chain-actions.v1", "action-outcomes.v1", "expected-outputs.v1"
    ]
  }
}
```

The capability set is defined in `quality-gate/descriptor.py`; the list above is
the current version-1 set, not an example. A consumer must reject a required
capability it does not understand.

The descriptor is generated from CLAD's shared parsers. Its capabilities are
additive within version 1; a consumer must reject an unknown contract name,
reject an unsupported major version, and reject any required capability it does
not understand. It may ignore optional fields it does not use.

`expectedOutputs` is keyed by **canonical stage id** (`01`, `01a`, `01b`,
`02`, `03`, `03a`, `03b`, `04b`), matching `clad_stages.py`. It lists only
outputs derivable at design time; profile-dependent side effects (`04a`
storage mappings, `04c` features and step definitions, `04d`/`04e`
implementation, `05` evidence) are intentionally omitted rather than guessed.

This is a compatibility boundary, not a second source of truth:

- Markdown artefacts remain the reviewable source of truth.
- `describe_feature.py` is the canonical machine projection.
- Quality gates and generators consume the same parser data as the projection.
- A consumer failure must be explicit and fail closed; it must not silently
  fall back to Java-side Markdown parsing for a known descriptor field.

Future incompatible changes require a new descriptor major version and a
corresponding capability set. Compatible additions keep version 1 and add a
capability or optional field. The CLAD release notes must mention either
change so `clad-agent` can update its supported contract range deliberately.