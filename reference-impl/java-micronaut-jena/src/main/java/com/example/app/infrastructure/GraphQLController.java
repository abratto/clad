package com.example.app.infrastructure;

import com.example.app.engine.ActionRecord;
import com.example.app.engine.FlowManager;
import com.example.app.engine.ResponseAssembler;
import com.example.app.engine.SyncDispatcher;
import graphql.ExecutionInput;
import graphql.GraphQL;
import graphql.schema.DataFetcher;
import graphql.schema.GraphQLSchema;
import graphql.schema.GraphQLScalarType;
import graphql.schema.idl.RuntimeWiring;
import graphql.schema.idl.SchemaGenerator;
import graphql.schema.idl.SchemaParser;
import graphql.schema.idl.TypeDefinitionRegistry;
import io.micronaut.core.io.ResourceResolver;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import io.swagger.v3.oas.annotations.Hidden;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;

/**
 * GraphQL transport adapter. Loads a declarative schema at startup and wires
 * every query/mutation to the same {@link FlowManager#rootAction} →
 * {@link SyncDispatcher#awaitResponse} engine pipeline used by REST controllers.
 *
 * <p>Demonstrates ports-and-adapters: the CLAD engine is surface-agnostic.
 * Same login flow token, same response shape, different query language.
 */
@Hidden
@Controller
@Singleton
public class GraphQLController {

    private static final GraphQLScalarType JSON_SCALAR = GraphQLScalarType.newScalar()
            .name("JSON")
            .description("JSON scalar")
            .coercing(new graphql.schema.Coercing<Object, Object>() {
                @Override public Object serialize(Object dataFetcherResult) { return dataFetcherResult; }
                @Override public Object parseValue(Object input) { return input; }
                @Override public Object parseLiteral(Object input) { return input; }
            })
            .build();

    private final AtomicReference<GraphQL> graphQL = new AtomicReference<>();
    private final FlowManager flowManager;
    private final SyncDispatcher syncDispatcher;
    private final ResponseAssembler responseAssembler;
    private volatile String initError;

    @Inject
    public GraphQLController(FlowManager flowManager, SyncDispatcher syncDispatcher,
                             ResponseAssembler responseAssembler) {
        this.flowManager = flowManager;
        this.syncDispatcher = syncDispatcher;
        this.responseAssembler = responseAssembler;
        try {
            this.graphQL.set(buildGraphQL(flowManager, syncDispatcher, responseAssembler));
        } catch (Exception e) {
            this.initError = e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
        }
    }

    private static final ThreadLocal<String> lastFlowToken = new ThreadLocal<>();

    @Post(value = "/graphql", produces = MediaType.APPLICATION_JSON)
    public HttpResponse<?> handle(@Body Map<String, Object> body) {
        if (graphQL.get() == null) {
            return HttpResponse.serverError(Map.of("error",
                    "GraphQL not initialized: " + (initError != null ? initError : "unknown")));
        }
        String query = (String) body.get("query");
        if (query == null) return HttpResponse.badRequest(Map.of("error", "query is required"));
        try {
            var input = ExecutionInput.newExecutionInput().query(query).build();
            var result = graphQL.get().execute(input);
            var responseBody = new LinkedHashMap<String, Object>();
            if (result.getData() != null) responseBody.put("data", result.getData());
            if (!result.getErrors().isEmpty()) {
                var errors = result.getErrors().stream()
                        .map(e -> Map.of("message",
                                e.getMessage() != null ? e.getMessage() : "null-message"))
                        .toList();
                responseBody.put("errors", errors);
            }
            var response = HttpResponse.ok(responseBody);
            String ft = lastFlowToken.get();
            if (ft != null) response.header(SyncDispatcher.FLOW_TOKEN_HEADER, ft);
            return response;
        } catch (Exception e) {
            return HttpResponse.ok(Map.of("errors",
                    java.util.List.of(Map.of("message",
                            e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName()))));
        } finally {
            lastFlowToken.remove();
        }
    }

    @Get(value = "/graphql/status", produces = MediaType.APPLICATION_JSON)
    public HttpResponse<?> status() {
        return HttpResponse.ok(Map.of(
                "initialized", graphQL.get() != null,
                "error", initError != null ? initError : ""));
    }

    private static Map<String, String> execFlow(FlowManager fm, SyncDispatcher sd,
                                                   ResponseAssembler ra, String name,
                                                   Map<String, String> params) {
        ActionRecord root = fm.rootAction(name, params);
        lastFlowToken.set(root.flowToken());
        try {
            var resp = sd.awaitResponse(root.flowToken()).toFuture().get();
            var code = resp.getStatus().getCode();
            var fields = new LinkedHashMap<String, String>();
            fields.put("_status", String.valueOf(code));
            if (code / 100 == 2 && resp.body() instanceof Map<?,?> m) {
                m.forEach((k, v) -> fields.put(k.toString(), v != null ? v.toString() : ""));
            }
            return fields;
        } catch (Exception e) {
            var fields = new LinkedHashMap<String, String>();
            fields.put("_status", "exception");
            fields.put("message", e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName());
            return fields;
        }
    }

    private static DataFetcher<?> inputFetcher(FlowManager fm, SyncDispatcher sd,
                                            ResponseAssembler ra, String flowName,
                                            String inputObjName, String... argNames) {
        return env -> {
            LinkedHashMap<String, String> params = new LinkedHashMap<>();
            for (String name : argNames) {
                Object input = env.getArgument(inputObjName);
                if (input instanceof Map) {
                    Object val = ((Map<?, ?>) input).get(name);
                    if (val != null) params.put(name, val.toString());
                }
            }
            var f = execFlow(fm, sd, ra, flowName, params);
            String s = f.remove("_status");
            if (s != null && !s.startsWith("2")) {
                throw new RuntimeException("username or password didn't match");
            }
            return ra.assemble(flowName, f);
        };
    }

    private static GraphQL buildGraphQL(FlowManager fm, SyncDispatcher sd, ResponseAssembler ra) {
        String sdl = loadSchema();
        TypeDefinitionRegistry registry = new SchemaParser().parse(sdl);
        RuntimeWiring wiring = RuntimeWiring.newRuntimeWiring()
                .type("Query", w -> w
                        .dataFetcher("flows", env -> Map.of())
                        .dataFetcher("stuck", env -> Map.of()))
                .type("Mutation", w -> w
                        .dataFetcher("login", inputFetcher(fm, sd, ra, "login",
                                "loginRequestInput", "username", "password"))
                        .dataFetcher("loginLegacy", inputFetcher(fm, sd, ra, "login",
                                "loginRequestInput", "username", "password")))
                .scalar(JSON_SCALAR)
                .build();
        GraphQLSchema schema = new SchemaGenerator().makeExecutableSchema(registry, wiring);
        return GraphQL.newGraphQL(schema).build();
    }

    private static String loadSchema() {
        var resolver = new ResourceResolver();
        var resource = resolver.getResource("classpath:graphql/schema.graphqls");
        if (resource.isEmpty()) throw new RuntimeException("graphql/schema.graphqls not found");
        try (var reader = new BufferedReader(
                new InputStreamReader(resource.get().openStream(), StandardCharsets.UTF_8))) {
            return reader.lines().collect(Collectors.joining("\n"));
        } catch (Exception e) {
            throw new RuntimeException("Failed to load GraphQL schema: " + e.getMessage(), e);
        }
    }
}
