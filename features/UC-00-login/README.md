# UC-00 — Login

A worked example use case. It is the simplest thing CLAD can be applied
to that is still meaningfully more than a "hello world": authenticate a
user with a username and a password, and on success establish a
session token they can present on subsequent requests.

It is intended for **reading**, not running. The point is to show the
shape of a feature folder under CLAD/Legible/ICM, end to end.

## What's here

- [`_config/voice.md`](_config/voice.md) — feature-scoped reference (e.g. tone of error messages)
- [`stages/01_usecase/`](stages/01_usecase/) — the use case spec
- [`stages/02_concepts/`](stages/02_concepts/) — three concepts: `User`, `PasswordAuth`, `Session`
- [`stages/03_syncs/`](stages/03_syncs/) — one sync: login → session
- [`stages/04_implement/`](stages/04_implement/) — placeholder; would land code under `reference-impl/`
- [`stages/05_verify/`](stages/05_verify/) — placeholder; would walk flow tokens against the use case

## Status

Seed. Stages 1–3 have full artefacts. Stages 4–5 have `CONTEXT.md` files
showing what they would do, with empty `output/` directories.
