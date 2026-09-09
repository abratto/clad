# reference-impl/java-plain/

The **plain Java quick-start**: one module, zero framework. The fire-after-commit engine, one `FactStore`, the login feature's three concepts, `Web` bootstrap, and the seven syncs — and nothing else. No DI, no HTTP server: the transport surface is a method call.

| Layer | Technology |
|---|---|
| Language | Java 21 |
| Engine | `legible-engine` (fire-after-commit, in-memory `FactStore`) |
| DI / HTTP | none — `LoginApp.login(username, password)` **is** the port |
| Tests | JUnit 5 |
| Feature set | login only (4 scenarios) |

## Run it

```bash
mvn -pl java-plain -am test            # concept + flow + concurrency tests
mvn -pl java-plain -am exec:java       # interactive demo (PlainDemoApp)
```

Demo keys: `seed`, `success`, `wrong-password`, `unknown-user`, `lockout`, `quit`.

## Why this profile exists

It is the smallest complete CLAD example — the thing to read first and the
thing to copy from when starting a project under the methodology. The whole
application is five files:

| File | Role |
|---|---|
| `login/WebConcept.java` | bootstrap concept (`request` / `respond`) — entry/exit only |
| `login/UserNamingConcept.java` | usernames → opaque `UserId` |
| `login/PasswordAuthConcept.java` | credential check, lockout (deterministic hash — **do not use in production**) |
| `login/SessionConcept.java` | bearer-token sessions |
| `login/LoginSyncs.java` | the seven declarative syncs (1:1 with the Stage 03 `*.sync.md` files) |

`LoginApp` wires them: one store, one engine, four concepts, seven rules.

## Copy-out scaffold for a new project

1. Copy `legible-engine/src/main/java/dev/legible/engine/` **verbatim** into
   `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/engine/`, changing only the package
   declaration. Never author engine classes from scratch.
2. Copy the login concept/sync classes as your pattern, then rename them to
   your own concepts and syncs.
3. Boot the same way `LoginApp.create()` does:
   one `FactStore`, though this profile keeps it `InMemoryFactStore`.

### Compile harder than the example

The canonical engine ships its tests in `legible-engine`'s test set: parity,
concurrency, and flow-token lineage. Copy `ConceptTest` / `FlowTraceTest` /
`ConcurrencyTest` here as the model for your own concept + flow stages.

## Not included by design

No persistence (in-memory only — for durable state use the re-lowered
[`java-micronaut-postgres`](../java-micronaut-postgres/) profile), no HTTP
(transport surfaces belong to adapter-bearing profiles), no multi-feature
catalogue (see [`java-legible`](../java-legible/) for the full sync model:
fan-out, Pattern D reads, `OPTIONAL`, `?_eachthen`, route filters).
