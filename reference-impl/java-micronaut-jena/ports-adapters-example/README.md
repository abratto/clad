# Ports & Adapters — CLAD Reference Implementation Example

This directory demonstrates how the CLAD engine (concepts + syncs) can
serve multiple transport surfaces through ports and adapters without
modifying the core engine.

## What this example shows

| Surface | How to use | What happens |
|---|---|---|
| **REST** | `curl -X POST localhost:8080/api/login -d '{"username":"ada","password":"correct-horse-battery-staple"}'` | Returns `{"sessionToken":"..."}` with `X-Flow-Token` header |
| **GraphQL** | `curl -X POST localhost:8080/graphql -d '{"query":"mutation { login(loginRequestInput:{username:\\"ada\\",password:\\"correct-horse-battery-staple\\"}) { sessionToken } }"}'` | Same sessionToken, same engine path |
| **OpenAPI** | Open `localhost:8080/swagger-ui` | Interactive API docs generated from `openapi/login-api.yaml` |
| **Web UI** | Open `localhost:8080/login.html` | Simple form calling `POST /api/login` via `fetch()` |
| **Mobile** | `cd mobile && flutter run` | Login screen on emulator calling the same endpoint |

### Multi-surface proof

```
$ mvn test
→ MultiSurfaceConsistencyTest: 5 tests, all green
  ✓ REST returns sessionToken
  ✓ REST returns 401 for wrong password
  ✓ GraphQL returns sessionToken
  ✓ GraphQL status endpoint
  ✓ REST and legacy endpoints produce identical responses
→ OpenApiDocsTest: 3 tests, all green
  ✓ OpenAPI spec served and contains login endpoints
  ✓ Swagger UI redirects
  ✓ Login page served
```

## Architecture

```
   POST /api/login        POST /graphql       POST /login (legacy)
         │                      │                     │
         ▼                      ▼                     ▼
   AuthController.java   GraphQLController.java   WebController.java
         │                      │                     │
         └──────────────────────┼─────────────────────┘
                                │
                                ▼
                     FlowManager.rootAction()
                                │
                                ▼
                     SyncDispatcher.awaitResponse()
                     (concepts + syncs + RDF engine)
                                │
                                ▼
                     ResponseAssembler.assemble()
                     (Map<String,String> → typed DTO)
```

Every transport adapter follows the same 3-line contract:
1. `FlowManager.rootAction(flowName, params)` — mint flow token
2. `SyncDispatcher.awaitResponse(flowToken)` — drive engine
3. `ResponseAssembler.assemble(flowName, fields)` — map to DTOs

Zero business logic in controllers. The CLAD engine is surface-agnostic.

## Files

| File | Role |
|---|---|
| `AuthController.java` | REST adapter at `/api/login` |
| `GraphQLController.java` | GraphQL adapter at `/graphql` |
| `OpenApiDocsController.java` | Swagger UI + OpenAPI spec serving |
| `ResponseAssembler.java` | Engine output → typed DTO mapping |
| `graphql/schema.graphqls` | Declarative GraphQL schema |
| `public/login.html` | Web UI adapter |
| `openapi/login-api.yaml` | Declarative REST contract |
| `MultiSurfaceConsistencyTest.java` | Proves REST = GraphQL |
| `OpenApiDocsTest.java` | Verifies spec + UI |
| `mobile/` | Flutter mobile adapter |

## Running

```bash
cd reference-impl/java-micronaut-jena
mvn test                    # All 40+ tests pass
mvn compile exec:java       # Boot the app on port 8080
```

## CLI smoke

```bash
# REST
curl -X POST localhost:8080/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ada","password":"correct-horse-battery-staple"}'

# GraphQL
curl -X POST localhost:8080/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"mutation { login(loginRequestInput:{username:\"ada\",password:\"correct-horse-battery-staple\"}) { sessionToken } }"}'

# Open browser
open http://localhost:8080/swagger-ui
open http://localhost:8080/login.html
```

## Relationship to CLAD methodology

This example does **not** modify CLAD methodology, rules, or stage
contracts. It demonstrates implementation patterns (ports and adapters)
that layer on top of the CLAD engine without changing architecture.
All CLAD hard rules (R1–R9) still apply.

## Web UI alternatives

The login page is served by `StaticPageController` — a thin Micronaut
controller that reads `public/login.html` from the classpath. No
business logic, no backend dependencies.

For richer frontends, a dedicated web framework can be added as a
separate project. [clad-pharmacy](https://github.com/abratto/clad-pharmacy)
demonstrates a complete 14-page Next.js 16 + React 19 + TypeScript
frontend consuming the same OpenAPI spec and CLAD engine — same engine,
same flow tokens, different frontend framework. The Next.js app is a
thin UI adapter with zero business logic, just like the single-page
`login.html` served here.
