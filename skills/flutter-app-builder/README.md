# Flutter App Builder Skill for Claude Code

> **Status: Work In Progress** — This skill is actively being developed. Patterns and APIs may change.

A skill that enables Claude Code to build Flutter applications using the right architecture for the project's complexity — no over-engineering for small apps, no under-engineering for production ones.

## Overview

This skill gives Claude comprehensive knowledge of modern Flutter development patterns, including:

- **Complexity-aware architecture** that selects Simple or Production patterns based on project signals
- **BLoC/Cubit state management** at every tier using `flutter_bloc`
- **Page/Screen separation** so BlocProviders own lifecycle and Screens stay pure UI
- **Clean Architecture** with UI, Domain, and Data layers (Tier 2)
- **Offline-first data layer** with Drift (SQLite) and Dio (Tier 2)
- **Dependency injection** with `get_it` (Tier 1) or `get_it + injectable` with code generation (Tier 2)
- **Type-safe navigation** with `go_router` and `GoRouteData` (Tier 2) or string routes (Tier 1)

## How It Works

The skill is invoked automatically by Claude Code when you work on Flutter projects. Claude detects the complexity tier from project signals before writing any code, then applies the matching architecture blueprint.

Simply ask Claude to:

- "Create a new Flutter app for tracking habits"
- "Add a user profile feature to my Flutter app"
- "Build a Cubit for my shopping cart screen"
- "Set up a repository with Drift and Dio"
- "Configure go_router with type-safe routes"

Claude will apply the correct tier automatically, or ask a single clarifying question when ambiguous.

## Tier Summary

| | Tier 1 — Simple | Tier 2 — Production |
|-|-----------------|---------------------|
| **When to use** | Personal/prototype, 1–3 features, solo dev | Real app, 3+ features, team or production release |
| **Structure** | Flat feature packages under `lib/` | Feature-based packages with `data/`, `domain/`, `presentation/` |
| **State** | Plain Dart sealed classes | `freezed` sealed classes |
| **Cubit/BLoC** | Cubit, manual constructor injection | BLoC or Cubit, `@injectable` annotation |
| **DI** | Manual DI via constructor in `main.dart` | `get_it + injectable`, code generation |
| **Navigation** | `go_router` string/path routes | `go_router` with `GoRouteData` + `@TypedGoRoute` |
| **Persistence** | `shared_preferences` (key-value) | `drift` (SQLite), `shared_preferences` optional |
| **Networking** | Optional `dio` | `dio` with remote datasource pattern |
| **Code generation** | None | `build_runner` (freezed + injectable + drift) |
| **Repository** | Concrete class, no interface required | Abstract interface + `@LazySingleton` implementation |

## Reference Documentation

| Topic | File | Description |
|-------|------|-------------|
| Complexity Tiers | [references/complexity-tiers.md](references/complexity-tiers.md) | Tier detection heuristics and full blueprints |
| Architecture | [references/architecture.md](references/architecture.md) | UI, Domain, Data layers and clean architecture |
| BLoC Patterns | [references/bloc-patterns.md](references/bloc-patterns.md) | BLoC/Cubit patterns, events, state transitions |
| Navigation | [references/navigation.md](references/navigation.md) | go_router setup, typed routes, deep linking |
| Data Layer | [references/data-layer.md](references/data-layer.md) | Drift, Dio, repository pattern, offline-first |
| Dependency Injection | [references/di.md](references/di.md) | get_it setup, injectable annotations, scopes |
| Testing | [references/testing.md](references/testing.md) | Unit tests, widget tests, test doubles |

## Technology Stack

| Concern | Tier 1 | Tier 2 |
|---------|--------|--------|
| Language | Dart 3.6+ | Dart 3.6+ |
| Framework | Flutter 3.27+ | Flutter 3.27+ |
| State management | flutter_bloc 9.1.x (Cubit) | flutter_bloc 9.1.x (BLoC/Cubit) |
| Navigation | go_router 17.x | go_router 17.x |
| DI | get_it 9.x (manual) | get_it 9.x + injectable 2.x |
| Data classes | Plain Dart `const` constructors | freezed 2.x |
| Persistence | shared_preferences | drift 2.x (SQLite) |
| Networking | dio 5.x (optional) | dio 5.x |
| Code generation | None | build_runner 2.x |
