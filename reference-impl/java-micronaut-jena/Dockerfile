FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:resolve -B
COPY src/ src/
RUN mvn package -DskipTests -B && \
    mvn dependency:copy-dependencies -DoutputDirectory=target/lib -B

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/clad-*.jar app.jar
COPY --from=build /app/target/lib/ target/lib/
COPY --from=build /app/target/classes/ target/classes/
EXPOSE 8080
ENTRYPOINT ["java", "-cp", "app.jar:target/lib/*:target/classes", "com.example.app.Application"]
