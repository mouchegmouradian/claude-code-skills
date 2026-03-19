# Complexity Tiers

This document defines the two architecture tiers used by the Flutter app builder skill.
When SKILL.md detects a tier, it refers here for the complete blueprint.

## Table of Contents

1. [Tier Decision Matrix](#tier-decision-matrix)
2. [Tier 1 — Simple](#tier-1--simple)
3. [Tier 2 — Production](#tier-2--production)
4. [Detection Heuristics (Extended)](#detection-heuristics-extended)
5. [Migration Path: Tier 1 → Tier 2](#migration-path-tier-1--tier-2)

---

## Tier Decision Matrix

| Signal | Tier 1 — Simple | Tier 2 — Production |
|---|---|---|
| Feature count | 1–4 | 5+ |
| Inter-feature data sharing | None or minimal | Complex (multiple repos, use cases) |
| Persistence | shared_preferences or Drift (simple) | Drift with typed DAOs and migrations |
| Team size | Solo / personal | 2+ devs |
| DI framework | Manual (no get_it) | get_it + injectable |
| freezed | No — plain Dart sealed classes | Yes — freezed for all states, events, entities |
| Code generation | No build_runner | build_runner (injectable, freezed, drift_dev) |
| Module structure | Feature packages in `lib/` | Clean architecture layers per feature |
| Prototype / demo | Yes → Tier 1 | No |

---

## Tier 1 — Simple

### When to Use

- Personal apps, demos, prototypes, learning projects
- 1–4 features where no feature needs data from another feature
- Solo developer
- Time-to-first-screen matters more than long-term maintainability
- You want zero build_runner ceremony

### What You Get

- Feature packages under `lib/features/`
- No get_it — repository injected manually via `BlocProvider`
- No freezed — plain Dart sealed classes for state
- No build_runner — zero code-generation overhead
- Cubit (not BLoC) — simpler emit-based state management
- shared_preferences for lightweight persistence or Drift with a single DAO
- Simple go_router string paths (no type-safe route codegen)
- Repository is a concrete class; no interface required

### What You Do NOT Get (by Design)

- get_it service locator / injectable annotations
- freezed union types
- Code generation (build_runner, injectable_generator, drift_dev)
- Clean architecture layers (domain, data, presentation)
- Use case classes
- Type-safe go_router routes

### File Structure

```
lib/
├── main.dart
├── app.dart
├── router.dart
├── data/
│   └── item_repository.dart   # Concrete class, no interface
└── features/
    └── featurename/
        ├── feature_page.dart
        ├── feature_screen.dart
        ├── feature_cubit.dart
        └── feature_state.dart
```

### `pubspec.yaml` Dependencies (Tier 1)

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^9.1.1
  go_router: ^17.1.0
  shared_preferences: ^2.5.4
  # Add drift + drift_flutter only if you need structured local storage:
  # drift: ^2.32.0
  # drift_flutter: ^0.3.0
  # sqlite3: ^3.2.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^6.0.0
  # NO build_runner
  # NO injectable_generator
  # NO freezed
  # NO drift_dev
```

No `build_runner`, no `injectable`, no `freezed`. This is intentional.

### Cubit Pattern (No freezed)

```dart
// feature_state.dart - plain sealed classes
sealed class FeatureState {}
class FeatureInitial extends FeatureState {}
class FeatureLoading extends FeatureState {}
class FeatureSuccess extends FeatureState {
  final List<Item> items;
  FeatureSuccess(this.items);
}
class FeatureError extends FeatureState {
  final String message;
  FeatureError(this.message);
}

// feature_cubit.dart
class FeatureCubit extends Cubit<FeatureState> {
  FeatureCubit(this._repository) : super(FeatureInitial());
  final ItemRepository _repository;

  Future<void> loadItems() async {
    emit(FeatureLoading());
    try {
      final items = await _repository.getItems();
      emit(FeatureSuccess(items));
    } catch (e) {
      emit(FeatureError(e.toString()));
    }
  }
}
```

### Page / Screen Pattern (Manual DI)

```dart
// feature_page.dart - owns Cubit, wires DI
class FeaturePage extends StatelessWidget {
  const FeaturePage({super.key});
  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (_) => FeatureCubit(ItemRepository())..loadItems(),
    child: const FeatureScreen(),
  );
}

// feature_screen.dart - pure UI
class FeatureScreen extends StatelessWidget {
  const FeatureScreen({super.key});
  @override
  Widget build(BuildContext context) => BlocBuilder<FeatureCubit, FeatureState>(
    builder: (context, state) => switch (state) {
      FeatureInitial() || FeatureLoading() => const CircularProgressIndicator(),
      FeatureSuccess(:final items) => ListView.builder(
        itemCount: items.length,
        itemBuilder: (_, i) => ListTile(title: Text(items[i].name)),
      ),
      FeatureError(:final message) => Text(message),
    },
  );
}
```

### `main.dart` Wiring

```dart
void main() {
  runApp(const MyApp());
}
```

No `WidgetsFlutterBinding.ensureInitialized()` unless you need platform channels before `runApp`.
No `configureDependencies()`. No service locator setup.

### Simple go_router (String Paths)

```dart
final router = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (_, __) => const FeaturePage()),
    GoRoute(
      path: '/detail/:id',
      builder: (ctx, state) => DetailPage(id: state.pathParameters['id']!),
    ),
  ],
);
```

> Tier 1 uses string paths for simplicity. Tier 2 uses type-safe routes with go_router codegen.

### Testing (Tier 1)

- Cubit: construct directly with a concrete fake repository, use `bloc_test` and `expect`
- No injectable setup, no service locator to configure in tests
- Screen: pump `BlocProvider` with a pre-seeded state and assert widget tree directly
- No `build_runner` needed — plain Dart constructs test immediately

### Graduation Trigger → Tier 2

Move to Tier 2 when:

- You need to inject the same repository into more than 2 Cubits, **or**
- You add a 5th feature that shares domain logic with an existing feature, **or**
- Business logic grows complex enough that Cubit event sequencing becomes hard to track, **or**
- Multiple developers need clear layer boundaries to work in parallel

---

## Tier 2 — Production

### When to Use

- Real apps with 5+ features
- Multi-developer teams where layer ownership matters
- Features share domain logic or repository state
- Persistence required (Drift with typed tables and migrations)
- Remote API calls (Dio)
- You want compile-time wiring safety (injectable) and immutable data (freezed)

### What You Get

- Clean architecture layers per feature: `data/`, `domain/`, `presentation/`
- get_it + injectable for compile-time safe DI with generated registration
- freezed for immutable states, events, entities, and DTOs
- Drift for structured local database with typed DAOs
- Dio for HTTP client
- BLoC (not Cubit) — full event + state separation for complex flows
- Type-safe go_router routes with codegen (`@TypedGoRoute`)
- Use case classes in `domain/usecases/`
- Abstract repository interfaces in `domain/repositories/`

### What You Do NOT Get (by Design)

- Multiple Flutter packages (monorepo) — single `lib/` tree with layer separation is sufficient
- riverpod (Tier 2 commits to BLoC/Cubit throughout)
- Generated network clients (use Dio manually; add retrofit only if explicitly requested)

### File Structure

```
lib/
├── main.dart                    # configureDependencies(), runApp
├── app.dart
├── injection.dart               # @InjectableInit
├── injection.config.dart        # generated
├── router/
│   ├── app_router.dart
│   └── app_router.g.dart        # generated
├── core/
│   └── usecase/
│       └── usecase.dart         # abstract base class
└── features/
    └── featurename/
        ├── data/
        │   ├── datasources/
        │   │   ├── local/       # Drift DAO
        │   │   └── remote/      # Dio client
        │   ├── models/          # DTOs (freezed)
        │   └── repositories/
        │       └── feature_repository_impl.dart
        ├── domain/
        │   ├── entities/
        │   │   └── feature_item.dart  # freezed
        │   ├── repositories/
        │   │   └── feature_repository.dart  # abstract interface
        │   └── usecases/
        │       └── get_items_usecase.dart
        └── presentation/
            ├── bloc/
            │   ├── feature_bloc.dart
            │   ├── feature_event.dart
            │   └── feature_state.dart
            ├── feature_page.dart
            └── feature_screen.dart
```

### `pubspec.yaml` Dependencies (Tier 2)

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^9.1.1
  go_router: ^17.1.0
  get_it: 9.2.1
  injectable: ^2.7.1+4
  freezed_annotation: ^3.1.0
  drift: ^2.32.0
  drift_flutter: ^0.3.0
  sqlite3: ^3.2.0
  dio: ^5.9.2
  shared_preferences: ^2.5.4

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^6.0.0
  build_runner: ^2.4.12
  injectable_generator: ^2.6.2
  freezed: ^2.5.7
  drift_dev: ^2.20.0
```

### BLoC Pattern with freezed

```dart
// feature_state.dart
part 'feature_state.freezed.dart';

@freezed
sealed class FeatureState with _$FeatureState {
  const factory FeatureState.loading() = _Loading;
  const factory FeatureState.success(List<FeatureItem> items) = _Success;
  const factory FeatureState.error(String message) = _Error;
}

// feature_event.dart
part 'feature_event.freezed.dart';

@freezed
sealed class FeatureEvent with _$FeatureEvent {
  const factory FeatureEvent.started() = _Started;
  const factory FeatureEvent.refreshed() = _Refreshed;
  const factory FeatureEvent.deleted(String id) = _Deleted;
}

// feature_bloc.dart
@injectable
class FeatureBloc extends Bloc<FeatureEvent, FeatureState> {
  FeatureBloc(this._getItems) : super(const FeatureState.loading()) {
    on<_Started>(_onStarted);
    on<_Refreshed>(_onStarted);
    on<_Deleted>(_onDeleted);
  }
  final GetItemsUseCase _getItems;

  Future<void> _onStarted(_Started event, Emitter<FeatureState> emit) async {
    emit(const FeatureState.loading());
    try {
      final items = await _getItems();
      emit(FeatureState.success(items));
    } catch (e) {
      emit(FeatureState.error(e.toString()));
    }
  }

  Future<void> _onDeleted(_Deleted event, Emitter<FeatureState> emit) async {
    // handle deletion...
  }
}
```

### Page Wiring with get_it

```dart
class FeaturePage extends StatelessWidget {
  const FeaturePage({super.key});
  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (_) => getIt<FeatureBloc>()..add(const FeatureEvent.started()),
    child: const FeatureScreen(),
  );
}
```

### `main.dart`

```dart
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  configureDependencies();
  runApp(const MyApp());
}
```

### Code Generation Command

Run after adding or modifying any `@injectable`, `@freezed`, or Drift table class:

```bash
dart run build_runner build --delete-conflicting-outputs
```

For development with continuous regeneration:

```bash
dart run build_runner watch --delete-conflicting-outputs
```

### Testing (Tier 2)

- BLoC: use `bloc_test` with `MockGetItemsUseCase` (mockito or manual fake)
- injectable: configure a test module that swaps real implementations for fakes
- Screen: pump `BlocProvider` with a manually constructed BLoC seeded to a known state
- Drift: use an in-memory database (`NativeDatabase.memory()`) in tests — no mocking needed

---

## Detection Heuristics (Extended)

These are the full reasoning rules. For the condensed version used during quick classification,
see `## Step 0: Detect Complexity Tier` in SKILL.md.

### Vocabulary Signals → Tier 1

- "demo", "prototype", "sample", "personal", "learning", "for fun", "side project", "proof of concept"
- "simple app", "basic app", "quick app"
- Single-screen or tab bar where each tab is fully independent (no shared data)
- No mention of teams, users, deployment, or backend
- Describes themselves as a beginner or student
- "I don't want to deal with code generation"

### Vocabulary Signals → Tier 2

- "production", "startup", "real app", "team", "multiple developers"
- Mentions a backend or API ("fetch from my server", "sync with a REST API", "Dio")
- Multiple features referencing the same data model ("list and detail for the same items across tabs")
- Mentions "clean architecture", "use cases", "repository pattern with interfaces"
- "I want get_it" or "I want freezed" — explicit request overrides heuristics
- "offline-first with local and remote data sources"

### Edge Cases

| Description | Tier | Reason |
|---|---|---|
| "I want to learn Flutter architecture" | 1 | Start simple; graduate as learning progresses |
| "Build me a to-do app" (no context) | Ask | Could be Tier 1 (personal) or Tier 2 (synced/multi-user) |
| "Build me a social media app" | 2 | Feed, profiles, notifications — shared data across features |
| "Build me a calculator" | 1 | Unconditionally simple |
| Small app but user explicitly requests get_it | 2 | Honor explicit request; note the decision |
| "An app with 5 features but they're totally independent" | 1 or 2 | Ask: do features share any repository or model? |
| "BLoC or Cubit?" with no other context | Ask | Both tiers use BLoC ecosystem; clarify scope first |

---

## Migration Path: Tier 1 → Tier 2

Steps in order:

1. Add dependencies to `pubspec.yaml`: `get_it`, `injectable`, `freezed_annotation`, `drift`, `drift_flutter`, `dio` (runtime) + `build_runner`, `injectable_generator`, `freezed`, `drift_dev` (dev)
2. Create `lib/injection.dart` with `@InjectableInit` and `configureDependencies()` call
3. Run `dart run build_runner build --delete-conflicting-outputs` to generate `injection.config.dart`
4. Update `main.dart` to call `WidgetsFlutterBinding.ensureInitialized()` and `configureDependencies()` before `runApp`
5. For each feature, introduce the domain layer:
   - Extract a repository interface in `domain/repositories/`
   - Create a use case class in `domain/usecases/`
   - Move the concrete repository to `data/repositories/` and annotate `@LazySingleton(as: FeatureRepository)`
6. Annotate each Cubit or BLoC with `@injectable`; replace manual `ItemRepository()` construction with injected constructor parameters
7. In each Page, replace `FeatureCubit(ItemRepository())` with `getIt<FeatureCubit>()`
8. Convert state and event classes from plain sealed classes to `@freezed` sealed classes; add `part` directives and regenerate
9. Migrate shared_preferences persistence to Drift if structured queries are needed:
   - Define `@DriftDatabase` class with table annotations
   - Move DAO logic to `data/datasources/local/`
   - Regenerate with build_runner
10. Switch go_router string paths to type-safe `@TypedGoRoute` annotations; regenerate `app_router.g.dart`

**Cost estimate:** 4–8 hours for a 3-feature Tier 1 app. The migration is well-defined and
mechanical. This is why it is not premature to use Tier 1 initially — the promotion path is
clear and bounded.
