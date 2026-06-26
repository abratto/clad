package com.example.app.infrastructure;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.swagger.v3.oas.annotations.Hidden;

import java.io.IOException;
import java.io.InputStream;
import java.util.Optional;

/**
 * Serves static HTML pages from classpath:public/.
 *
 * <p>For richer frontends, a dedicated web framework (e.g. Next.js) can
 * be used as a separate project — see ports-adapters-example/README.md.
 */
@Hidden
@Controller
final class StaticPageController {

    @Get(uri = "/login.html", produces = MediaType.TEXT_HTML)
    HttpResponse<String> loginPage() {
        return readText("public/login.html")
                .<HttpResponse<String>>map(HttpResponse::ok)
                .orElseGet(HttpResponse::notFound);
    }

    private static Optional<String> readText(String resourcePath) {
        try (InputStream input = StaticPageController.class.getClassLoader()
                .getResourceAsStream(resourcePath)) {
            if (input == null) return Optional.empty();
            return Optional.of(new String(input.readAllBytes(),
                    java.nio.charset.StandardCharsets.UTF_8));
        } catch (IOException e) {
            return Optional.empty();
        }
    }
}
