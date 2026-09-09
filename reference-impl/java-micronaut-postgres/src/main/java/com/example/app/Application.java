package com.example.app;

import io.micronaut.runtime.Micronaut;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;

@OpenAPIDefinition(
        info = @Info(
                title = "CLAD Java Reference API",
                version = "0.1.0",
                description = "Transport-facing REST surface for the CLAD Java/Micronaut/Postgres reference profile (fire-after-commit engine). This OpenAPI document is derived from the Web boundary and remains subordinate to CLAD use case, concept, sync, and SPEC artefacts."))
public class Application {

    public static void main(String[] args) {
        Micronaut.run(Application.class, args);
    }
}
