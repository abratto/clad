# Build the re-lowered CLAD reference profile jar, then run it as a container.
# Usage:
#   cd reference-impl/java-micronaut-postgres
#   docker compose up --build
#
# The build context is the repository root so the Maven reactor can build
# legible-engine + legible-storage alongside this module.

FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY reference-impl/pom.xml reference-impl/pom.xml
COPY reference-impl/clad-engine/ reference-impl/clad-engine/
COPY reference-impl/legible-engine/ reference-impl/legible-engine/
COPY reference-impl/legible-storage/ reference-impl/legible-storage/
COPY reference-impl/java-micronaut-postgres/ reference-impl/java-micronaut-postgres/
COPY reference-impl/java-legible/ reference-impl/java-legible/
COPY reference-impl/java-micronaut-jena/pom.xml reference-impl/java-micronaut-jena/pom.xml
COPY reference-impl/legible-bench/pom.xml reference-impl/legible-bench/pom.xml
COPY reference-impl/java-plain/pom.xml reference-impl/java-plain/pom.xml
WORKDIR /app/reference-impl/java-micronaut-postgres
RUN mvn -f /app/reference-impl/pom.xml -pl java-micronaut-postgres -am install -DskipTests -B && \
    mvn dependency:copy-dependencies -B -DincludeScope=runtime

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/reference-impl/java-micronaut-postgres/target/clad-java-micronaut-postgres-*.jar app.jar
COPY --from=build /app/reference-impl/java-micronaut-postgres/target/dependency/ target/lib/
COPY --from=build /app/reference-impl/java-micronaut-postgres/target/classes/ target/classes/
EXPOSE 8080
ENTRYPOINT ["java", "-cp", "app.jar:target/lib/*:target/classes", "com.example.app.Application"]
