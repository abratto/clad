package com.example.app.infrastructure;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.MutableHttpResponse;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.swagger.v3.oas.annotations.Hidden;

import java.io.IOException;
import java.io.InputStream;
import java.util.Optional;

/**
 * Serves the OpenAPI spec and Swagger UI. The spec is a declarative
 * transport contract that complements CLAD's declarative sync layer.
 */
@Hidden
@Controller
final class OpenApiDocsController {

    private static final String OPENAPI_SPEC = "META-INF/swagger/empower-patient-api-0.1.0.yml";
    private static final String OPENAPI_SPEC_ALT = "META-INF/swagger/clad-java-reference-api-0.1.0.yml";
    private static final String SWAGGER_UI_ROOT = "META-INF/swagger/views/swagger-ui/";

    @Get(uri = "/swagger/empower-patient-api-0.1.0.yml", produces = {"application/yaml", MediaType.TEXT_PLAIN})
    HttpResponse<String> openApiYaml() {
        return readText(OPENAPI_SPEC)
                .<HttpResponse<String>>map(HttpResponse::ok)
                .or(() -> readText(OPENAPI_SPEC_ALT).map(HttpResponse::ok))
                .orElseGet(HttpResponse::notFound);
    }

    @Get(uri = "/swagger-ui")
    HttpResponse<Object> swaggerUiRoot() {
        return HttpResponse.redirect(java.net.URI.create("/swagger-ui/index.html"));
    }

    @Get(uri = "/swagger-ui/{path:.*}")
    MutableHttpResponse<byte[]> swaggerUiAsset(String path) {
        if (path == null || path.isBlank() || path.contains("..")) {
            return HttpResponse.notFound();
        }
        return readBytes(SWAGGER_UI_ROOT + path)
                .map(bytes -> HttpResponse.ok(bytes).contentType(contentType(path)))
                .orElseGet(HttpResponse::notFound);
    }

    private static Optional<String> readText(String resourcePath) {
        return readBytes(resourcePath).map(bytes -> new String(bytes, java.nio.charset.StandardCharsets.UTF_8));
    }

    private static Optional<byte[]> readBytes(String resourcePath) {
        try (InputStream input = OpenApiDocsController.class.getClassLoader().getResourceAsStream(resourcePath)) {
            if (input == null) {
                return Optional.empty();
            }
            return Optional.of(input.readAllBytes());
        } catch (IOException e) {
            throw new IllegalStateException("Failed to read generated OpenAPI resource: " + resourcePath, e);
        }
    }

    private static MediaType contentType(String path) {
        if (path.endsWith(".html")) {
            return MediaType.TEXT_HTML_TYPE;
        }
        if (path.endsWith(".css")) {
            return MediaType.TEXT_CSS_TYPE;
        }
        if (path.endsWith(".js")) {
            return new MediaType("application/javascript");
        }
        if (path.endsWith(".png")) {
            return MediaType.IMAGE_PNG_TYPE;
        }
        return MediaType.APPLICATION_OCTET_STREAM_TYPE;
    }
}
