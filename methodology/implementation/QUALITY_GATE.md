# Quality gate — pre-commit checks

A **quality gate** is the small set of checks every commit on a CLAD
project must pass before being pushed. This file describes the
language-agnostic gate, then the gate as it applies to the
Java/Micronaut/Jena profile that ships with this starter.

The gate is intentionally small. A long gate that nobody runs is
worse than a short gate that everybody runs.

---

## Language-agnostic principles

These hold for every profile. Adapt the *commands* per profile; do
not relax the *intent*.

1. **Format clean.** Code is formatted by the profile's standard
   formatter; running the formatter changes nothing.
2. **Lint clean.** The profile's standard linter reports zero issues
   on the files in the diff. (Whole-tree lint cleanliness is a
   separate goal.)
3. **No `TODO`/`FIXME` without a tracked issue.** A `TODO` is fine if
   it cites a tracker entry (`TODO(#123): ...`); naked `TODO`s do not
   pass.
4. **Tests green.** All tests touched by the diff, plus the full
   flow-test suite for any feature whose stage 04c artefacts changed,
   pass locally.
5. **Hard-rule check passes.** Whatever mechanism the profile uses to
   enforce R1/R2/R4 (architecture tests, lint plugin, custom script)
   runs and is green. R1 is the easiest to break by accident; the
   gate is what catches it.
6. **Stage outputs not edited out-of-band.** If the diff modifies a
   `stages/NN_*/output/` file, the diff also reflects an
   `Owner stage = NN` so a reviewer can see which stage produced the
   change. Edits to a stage's output that did not come from re-running
   that stage are flagged.

## Java/Micronaut/Jena profile

The reference profile under `reference-impl/java-micronaut-jena/`
maps the principles above to:

| Principle | Command |
|---|---|
| Format clean | `mvn spotless:apply` (then `spotless:check` is part of `verify`) |
| Lint clean | bundled into `mvn verify` |
| Tests green | `mvn verify` runs unit + integration |
| Hard-rule check | `LegibleArchitectureRulesTest` (ArchUnit) runs as part of `mvn verify` |
| Smoke check (when relevant) | `mvn exec:java` then exercise the route per Stage 05 closure |

The single command that exercises the gate is:

```
mvn verify
```

If `mvn verify` is green and the diff has no naked `TODO`/`FIXME`,
the commit is gate-clean. Pre-push hooks may automate the check; the
hook is convenience, not the gate itself.

### What the ArchUnit rules enforce

`LegibleArchitectureRulesTest` codifies R1 and R4:

- No class under `com.example.app.concepts.<X>` may import a class
  under `com.example.app.concepts.<Y>` for any other concept `Y`.
- HTTP-entry annotations (e.g. `@Controller`, `@Get`, `@Post`) only
  appear inside the `infrastructure.WebController` package surface.

If you add new rules (e.g. R2 enforcement when an RDF profile is
wired), extend that test class. The test class is the codified form
of the rules in [`RULES.md`](RULES.md).

## Other profiles

A profile under `reference-impl/<other>/` that wants to claim CLAD
compliance must publish, in its `README.md`:

- The single command that runs the gate.
- The mechanism enforcing R1, R2, R4 (with a pointer to the file or
  test).
- Anything specific to that language's idioms (e.g. `mypy --strict`
  for Python, `tsc --noEmit` for TypeScript).

The expectation is that **one command** runs the whole gate. If a
profile needs five commands chained, it is not yet ready.
