# CLAD Login — Flutter Mobile Adapter

This Flutter app calls the same `POST /api/login` endpoint as the REST
and GraphQL surfaces. It demonstrates the ports-and-adapters pattern: the
CLAD engine is surface-agnostic.

## Prerequisites

- Flutter SDK 3.2+
- Android emulator or iOS simulator
- CLAD backend running on `localhost:8080` (`mvn compile exec:java`)

## Run

```bash
cd reference-impl/java-micronaut-jena/ports-adapters-example/mobile
flutter pub get
flutter run
```

The app connects to `http://10.0.2.2:8080/api/login` (Android emulator
localhost alias). For iOS simulator, change the URL in
`login_screen.dart` to `http://localhost:8080/api/login`.

## What it demonstrates

- Same login flow, same engine, same response shape as REST and GraphQL
- Thin UI adapter: no business logic in the Flutter code
- Code generation pipeline: the same `login-api.yaml` could drive
  `openapi-generator` to produce a typed Dart client
