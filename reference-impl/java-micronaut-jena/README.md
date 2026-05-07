# java-micronaut-jena — reference profile

A WYSIWID implementation profile in **Java 21**, using **Micronaut**
for the HTTP runtime and **Apache Jena** for per-concept persistence
and the flow-token log.

## Status

Skeleton. The full reference implementation lives in
[`abratto/tastetag`](https://github.com/abratto/tastetag) under
`reference-impl/java-micronaut-jena/`. It will be migrated here in a
follow-up PR; this folder exists in the seed to make the structure
clear and to give other profiles something to mirror.

## Conventions (when populated)

- **One Maven module per concept.** No cross-module dependencies
  between concept modules. (Enforced by the build.)
- **One named graph per concept.** Each concept reads and writes
  only the graph URI assigned to it.
- **`Web` is the only module that depends on Micronaut HTTP.** Other
  concepts depend only on Jena and the local sync runtime.
- **Syncs are declared in a small DSL** (annotation- or builder-based)
  whose `when/where/then` shape matches the spec form one-to-one.
- **Flow tokens** are RDF triples appended to a dedicated graph,
  queryable by SPARQL for stage-5 verification.

## Layout (planned)

```
java-micronaut-jena/
├── pom.xml                       Aggregator
├── platform/
│   ├── flow-tokens/              Flow-token model + appender
│   └── sync-runtime/             when/where/then runtime
├── concepts/
│   ├── user/
│   ├── password-auth/
│   ├── session/
│   └── web/                      The HTTP entry concept
└── verify/
    └── (SPARQL queries used by stages/05_verify/)
```

See [`../README.md`](../README.md) for how this profile sits within the
broader `reference-impl/` folder, and
[`../../methodology/implementation/RULES.md`](../../methodology/implementation/RULES.md)
for the rules every profile must honour.
