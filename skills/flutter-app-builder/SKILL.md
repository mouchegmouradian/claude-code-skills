---
name: flutter-app-builder
description: Create Flutter applications scaled to project complexity. Automatically detects whether to use a simple single-module architecture (manual DI, shared_preferences) or a full production structure with get_it+injectable, freezed, Drift, and clean architecture. Use when building Flutter apps with Dart, BLoC/Cubit, go_router, and MVVM-like patterns. Triggers on requests to create Flutter projects, screens, BLoCs, Cubits, repositories, feature modules, or when asked about Flutter architecture patterns.
---

# Flutter Development

Build Flutter applications following clean architecture principles, BLoC/Cubit state management, and complexity-appropriate patterns.

## Quick Reference

| Task | Reference File |
|------|----------------|
| **Complexity tier selection** | [complexity-tiers.md](references/complexity-tiers.md) |
| Architecture layers (UI, Domain, Data) | [architecture.md](references/architecture.md) |
| BLoC/Cubit patterns & state management | [bloc-patterns.md](references/bloc-patterns.md) |
| Navigation with go_router | [navigation.md](references/navigation.md) |
| Data layer (Drift, Dio, Repository) | [data-layer.md](references/data-layer.md) |
| Dependency injection (get_it, injectable) | [di.md](references/di.md) |
| Testing approach | [testing.md](references/testing.md) |

## Step 0: Detect Complexity Tier

**Before writing any code**, classify the project into one of two tiers. This determines every architectural decision that follows.

### Detection Heuristics

Apply these signals in order. The first confident match wins.

**Tier 1 — Simple** (default for ambiguous small projects):
- Described as: demo, prototype, personal app, learning project, side project, sample, or proof-of-concept
- 1–3 distinct user-facing features
- Features are independent — no described need to share data across screens
- Solo developer with no production deployment requirements
- No described need for background sync, complex caching, or multi-team workflow
- Examples: counter app, note-taking app, flashcard app, unit converter, habit tracker

**Tier 2 — Production**:
- 3+ distinct user-facing features, or
- Team or production release, or
- Needs testable DI (injectable), type-safe code generation, or clean architecture boundaries, or
- Complex local persistence (relational data, sync), or
- Existing codebase being extended with production expectations
- Examples: e-commerce app, social app, fitness tracker with sync, real-time chat app

### Fallback: Ask When Uncertain

If the description is ambiguous, ask **exactly one** clarifying question before proceeding:

> "To choose the right architecture, how many distinct features does this app need, and is this a personal/prototype app or something for a team or production release?"

Use the answer to re-apply the heuristics above.

### After Classification

State the selected tier and its rationale in one sentence before generating any code. Example:

> "This is a Tier 1 (Simple) project — a personal prototype with 2 features and no shared data layer."

Then follow **only** the blueprint for that tier. Do not mix patterns across tiers.

---

## Workflow Decision Tree

**After detecting the tier (see Step 0 above):**

**Tier 1 — Creating a new project?**
→ Single `lib/` folder with flat feature packages
→ Manual DI — pass dependencies via constructor in `main.dart` or router
→ No `injectable`, no `freezed`, no `build_runner`
→ `shared_preferences` for key-value storage; Drift only if explicitly needed
→ Plain Dart sealed classes for state
→ See [Simple Tier Patterns](#simple-tier-patterns-tier-1-only) below

**Tier 2 — Creating a new project?**
→ Feature-based package structure inside `lib/`
→ `get_it + injectable` for DI
→ `freezed` for all domain models and state classes
→ `drift` for local database; `dio` for networking
→ Type-safe `go_router` with `GoRouteData` + `@TypedGoRoute`
→ `build_runner` for code generation (freezed, injectable, drift)
→ See [Production Tier Patterns](#production-tier-patterns-tier-2-only) below

**Adding a new feature? (all tiers)**
→ Tier 1: Add a new package under `lib/features/featurename/`
→ Tier 2: Create full feature package with `data/`, `domain/`, `presentation/` layers

**Building UI screens? (all tiers)**
→ Always create Page + Screen separation (Page owns BlocProvider, Screen is pure UI)
→ Always use sealed state classes (Loading/Success/Error)

**Setting up data layer?**
→ Tier 1: Concrete class, no interface required for simple cases
→ Tier 2: Interface + implementation; read [data-layer.md](references/data-layer.md)

**Working with streams/async? (all tiers)**
→ Use `Stream<T>` for all data that changes over time
→ Cubits/BLoCs emit state — never expose mutable state directly

## Core Principles

1. **BLoC/Cubit for all tiers**: UI state is always managed by a BLoC or Cubit — never `setState` for business logic
2. **Page/Screen separation**: Page creates `BlocProvider` and wires DI; Screen is pure UI that reads state
3. **Sealed states**: Always model Loading/Success/Error as sealed classes (plain in Tier 1, freezed in Tier 2)
4. **Reactive streams**: Use `Stream<T>` for all data that changes over time
5. **No mocking libraries**: Use test doubles that implement the same interfaces
6. **Offline-first (Tier 2)**: Local Drift database is source of truth when network sync is required
7. **Clean architecture (Tier 2)**: UI → Domain (optional UseCases) → Data

## Architecture Layers

```
┌─────────────────────────────────────────┐
│              UI Layer                    │
│  (Flutter Widgets + BLoC/Cubit)         │
├─────────────────────────────────────────┤
│           Domain Layer                   │
│  (Use Cases - optional, Tier 2 only)    │
├─────────────────────────────────────────┤
│            Data Layer                    │
│  (Repositories + DataSources)            │
└─────────────────────────────────────────┘
```

> **Tier 2 only.** Domain layer with UseCases is optional and applies only when there is real reuse or transformation logic to encapsulate. Tier 1 projects connect the Cubit directly to the repository.

---

## Simple Tier Patterns (Tier 1 Only)

Use these patterns **only** when the project is classified as Tier 1. Do not add `injectable`, `freezed`, or code generation to Tier 1 projects.

### Project Structure (Tier 1)

```
lib/
├── main.dart                    # Entry point, DI wiring, router
├── app.dart                     # MaterialApp.router
├── router.dart                  # GoRouter configuration
├── data/
│   └── item_repository.dart     # Concrete class, no interface required
└── features/
    └── items/
        ├── item_page.dart       # Creates BlocProvider
        ├── item_screen.dart     # Pure UI with BlocBuilder
        ├── item_cubit.dart      # Cubit state machine
        └── item_state.dart      # Sealed state classes
```

### State Pattern (Tier 1 — Plain Sealed Classes, No freezed)

```dart
// item_state.dart
sealed class ItemState {}

class ItemInitial extends ItemState {}

class ItemLoading extends ItemState {}

class ItemLoaded extends ItemState {
  final List<Item> items;
  ItemLoaded(this.items);
}

class ItemError extends ItemState {
  final String message;
  ItemError(this.message);
}
```

### Cubit Pattern (Tier 1)

```dart
// item_cubit.dart
class ItemCubit extends Cubit<ItemState> {
  ItemCubit(this._repository) : super(ItemInitial());

  final ItemRepository _repository;

  Future<void> loadItems() async {
    emit(ItemLoading());
    try {
      final items = await _repository.getItems();
      emit(ItemLoaded(items));
    } catch (e) {
      emit(ItemError(e.toString()));
    }
  }

  Future<void> deleteItem(String id) async {
    await _repository.deleteItem(id);
    await loadItems();
  }
}
```

For very simple state (single value, no loading/error), a minimal Cubit is acceptable:

```dart
// counter_state.dart
sealed class CounterState {}
class CounterInitial extends CounterState {}
class CounterLoaded extends CounterState {
  final int count;
  CounterLoaded(this.count);
}

// counter_cubit.dart
class CounterCubit extends Cubit<CounterState> {
  CounterCubit() : super(CounterInitial());
  void increment() => emit(CounterLoaded(
    state is CounterLoaded ? (state as CounterLoaded).count + 1 : 1,
  ));
}
```

### Page/Screen Separation (Tier 1)

```dart
// item_page.dart — owns the Cubit via BlocProvider
class ItemPage extends StatelessWidget {
  const ItemPage({super.key});

  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (context) => ItemCubit(
      context.read<ItemRepository>(),
    )..loadItems(),
    child: const ItemScreen(),
  );
}

// item_screen.dart — pure UI, reads state via BlocBuilder
class ItemScreen extends StatelessWidget {
  const ItemScreen({super.key});

  @override
  Widget build(BuildContext context) => BlocBuilder<ItemCubit, ItemState>(
    builder: (context, state) => switch (state) {
      ItemInitial() => const SizedBox.shrink(),
      ItemLoading() => const Center(child: CircularProgressIndicator()),
      ItemLoaded(:final items) => ListView.builder(
          itemCount: items.length,
          itemBuilder: (context, index) => ListTile(title: Text(items[index].name)),
        ),
      ItemError(:final message) => Center(child: Text(message)),
    },
  );
}
```

> The Page/Screen split ensures the BloC/Cubit lifecycle is tied to the route, not a parent widget. Screen never creates or owns state — it only reads it.

### Repository Pattern (Tier 1 — Concrete Class)

```dart
// item_repository.dart
class ItemRepository {
  Future<List<Item>> getItems() async {
    // In-memory, shared_preferences, or simple local file
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList('items') ?? [];
    return raw.map(Item.fromJson).toList();
  }

  Future<void> saveItem(Item item) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList('items') ?? [];
    prefs.setStringList('items', [...raw, item.toJson()]);
  }

  Future<void> deleteItem(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList('items') ?? [];
    prefs.setStringList('items', raw.where((e) => e != id).toList());
  }
}
```

### Manual DI in main.dart (Tier 1)

```dart
// main.dart
void main() {
  final repository = ItemRepository();
  runApp(MyApp(repository: repository));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key, required this.repository});

  final ItemRepository repository;

  @override
  Widget build(BuildContext context) => RepositoryProvider.value(
    value: repository,
    child: MaterialApp.router(
      routerConfig: buildRouter(repository),
    ),
  );
}
```

### go_router Setup (Tier 1 — String Routes)

```dart
// router.dart
GoRouter buildRouter(ItemRepository repository) => GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (_, __) => const ItemPage(),
    ),
    GoRoute(
      path: '/detail/:id',
      builder: (context, state) => DetailPage(
        id: state.pathParameters['id']!,
      ),
    ),
  ],
);
```

> Tier 1 uses plain string path routes for simplicity. Tier 2 uses `GoRouteData` + `@TypedGoRoute` for compile-time safety.

### `pubspec.yaml` (Tier 1 — No Code Generation)

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^9.1.1
  go_router: ^17.1.0
  get_it: 9.2.1
  shared_preferences: ^2.5.4
  # drift: ^2.0.0  # only if explicitly needed for relational data

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^6.0.0
```

No `build_runner`, no `injectable`, no `freezed`. This is intentional.

---

## Production Tier Patterns (Tier 2 Only)

Use these patterns when the project is classified as Tier 2. Feature-based structure with `get_it + injectable`, `freezed`, and `build_runner`.

### Project Structure (Tier 2)

```
lib/
├── main.dart                    # Entry point, configureDependencies()
├── app.dart                     # MaterialApp.router
├── injection.dart               # get_it setup (@InjectableInit)
├── injection.config.dart        # Generated by injectable
├── router/
│   ├── app_router.dart          # GoRouter with all typed routes
│   └── app_router.g.dart        # Generated
├── core/
│   ├── error/                   # Failure types
│   └── usecase/                 # UseCase base class
├── features/
│   └── items/
│       ├── data/
│       │   ├── datasource/
│       │   │   ├── local/       # Drift DAO
│       │   │   └── remote/      # Dio API client
│       │   ├── models/          # DTOs (freezed)
│       │   └── repositories/   # ItemRepositoryImpl
│       ├── domain/
│       │   ├── entities/        # Item (freezed)
│       │   ├── repositories/    # ItemRepository (interface)
│       │   └── usecases/        # GetItemsUseCase (optional)
│       └── presentation/
│           ├── bloc/
│           │   ├── item_bloc.dart
│           │   ├── item_event.dart
│           │   └── item_state.dart
│           ├── item_page.dart
│           └── item_screen.dart
```

### freezed State + Event Classes (Tier 2)

```dart
// item_state.dart
@freezed
sealed class ItemState with _$ItemState {
  const factory ItemState.loading() = _Loading;
  const factory ItemState.success(List<Item> items) = _Success;
  const factory ItemState.error(String message) = _Error;
}

// item_event.dart
@freezed
sealed class ItemEvent with _$ItemEvent {
  const factory ItemEvent.started() = _Started;
  const factory ItemEvent.refreshed() = _Refreshed;
  const factory ItemEvent.deleted(String id) = _Deleted;
}
```

### BLoC Pattern (Tier 2 — With Injectable)

```dart
// item_bloc.dart
@injectable
class ItemBloc extends Bloc<ItemEvent, ItemState> {
  ItemBloc(this._repository) : super(const ItemState.loading()) {
    on<_Started>(_onStarted);
    on<_Refreshed>(_onStarted);
    on<_Deleted>(_onDeleted);
  }

  final ItemRepository _repository;

  Future<void> _onStarted(_Started event, Emitter<ItemState> emit) async {
    emit(const ItemState.loading());
    try {
      final items = await _repository.getItems();
      emit(ItemState.success(items));
    } catch (e) {
      emit(ItemState.error(e.toString()));
    }
  }

  Future<void> _onDeleted(_Deleted event, Emitter<ItemState> emit) async {
    await _repository.deleteItem(event.id);
    add(const ItemEvent.started());
  }
}
```

> Use BLoC (event-driven) in Tier 2 when the feature has multiple distinct events. Use Cubit when state transitions are simple method calls without complex event routing.

### Page/Screen Separation (Tier 2)

```dart
// item_page.dart — wires DI via getIt, owns BlocProvider
class ItemPage extends StatelessWidget {
  const ItemPage({super.key});

  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (context) => getIt<ItemBloc>()..add(const ItemEvent.started()),
    child: const ItemScreen(),
  );
}

// item_screen.dart — pure UI
class ItemScreen extends StatelessWidget {
  const ItemScreen({super.key});

  @override
  Widget build(BuildContext context) => BlocBuilder<ItemBloc, ItemState>(
    builder: (context, state) => switch (state) {
      _Loading() => const Center(child: CircularProgressIndicator()),
      _Success(:final items) => ListView.builder(
          itemCount: items.length,
          itemBuilder: (context, index) => ListTile(
            title: Text(items[index].name),
            trailing: IconButton(
              icon: const Icon(Icons.delete),
              onPressed: () => context.read<ItemBloc>().add(
                ItemEvent.deleted(items[index].id),
              ),
            ),
          ),
        ),
      _Error(:final message) => Center(child: Text(message)),
    },
  );
}
```

### Repository Interface + Implementation (Tier 2)

```dart
// domain/repositories/item_repository.dart
abstract interface class ItemRepository {
  Future<List<Item>> getItems();
  Stream<List<Item>> watchItems();
  Future<void> deleteItem(String id);
}

// data/repositories/item_repository_impl.dart
@LazySingleton(as: ItemRepository)
class ItemRepositoryImpl implements ItemRepository {
  ItemRepositoryImpl(this._localDataSource, this._remoteDataSource);

  final ItemLocalDataSource _localDataSource;
  final ItemRemoteDataSource _remoteDataSource;

  @override
  Future<List<Item>> getItems() async {
    try {
      final remote = await _remoteDataSource.fetchItems();
      await _localDataSource.upsertAll(remote);
    } catch (_) {
      // Fall through to local data on error
    }
    return _localDataSource.getItems();
  }

  @override
  Stream<List<Item>> watchItems() => _localDataSource.watchItems();

  @override
  Future<void> deleteItem(String id) => _localDataSource.deleteItem(id);
}
```

### freezed Domain Model (Tier 2)

```dart
// domain/entities/item.dart
@freezed
class Item with _$Item {
  const factory Item({
    required String id,
    required String name,
    required DateTime createdAt,
    @Default(false) bool isCompleted,
  }) = _Item;
}
```

### get_it + injectable Setup (Tier 2)

```dart
// injection.dart
import 'package:get_it/get_it.dart';
import 'package:injectable/injectable.dart';
import 'injection.config.dart';

final getIt = GetIt.instance;

@InjectableInit()
void configureDependencies() => getIt.init();

// main.dart
void main() {
  configureDependencies();
  runApp(const MyApp());
}
```

### Type-Safe go_router (Tier 2)

```dart
// router/app_router.dart

@TypedGoRoute<HomeRoute>(path: '/', routes: [
  TypedGoRoute<ItemDetailRoute>(path: 'items/:id'),
])
class HomeRoute extends GoRouteData {
  const HomeRoute();

  @override
  Widget build(BuildContext context, GoRouterState state) => const ItemPage();
}

class ItemDetailRoute extends GoRouteData {
  const ItemDetailRoute({required this.id});

  final String id;

  @override
  Widget build(BuildContext context, GoRouterState state) =>
      ItemDetailPage(id: id);
}

// Usage — navigate type-safely:
// const ItemDetailRoute(id: '123').go(context);
```

### `pubspec.yaml` (Tier 2 — With Code Generation)

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
  dio: ^5.9.2
  shared_preferences: ^2.5.4  # optional, for lightweight settings

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^6.0.0
  build_runner: ^2.4.0
  injectable_generator: ^2.0.0
  freezed: ^2.0.0
  drift_dev: ^2.0.0
```

Run code generation:

```bash
dart run build_runner build --delete-conflicting-outputs
```

---

## Creating a New Feature

### Tier 1

1. Create `lib/features/myfeature/` directory
2. Add `myfeature_state.dart` — plain sealed state classes
3. Add `myfeature_cubit.dart` — Cubit with constructor-injected repository
4. Add `myfeature_page.dart` — `BlocProvider` that creates the Cubit
5. Add `myfeature_screen.dart` — pure UI with `BlocBuilder`
6. Register route in `router.dart`

### Tier 2

1. Create `lib/features/myfeature/` with `data/`, `domain/`, `presentation/` sub-packages
2. Add domain entity (freezed) in `domain/entities/`
3. Add repository interface in `domain/repositories/`
4. Add repository implementation (`@LazySingleton`) in `data/repositories/`
5. Add local datasource (Drift DAO) in `data/datasource/local/`
6. Add remote datasource (Dio) in `data/datasource/remote/`
7. Add freezed state + event in `presentation/bloc/`
8. Add `@injectable` BLoC in `presentation/bloc/`
9. Add Page (getIt wiring) and Screen (pure UI) in `presentation/`
10. Add `GoRouteData` route class in `router/app_router.dart`
11. Run `dart run build_runner build --delete-conflicting-outputs`

---

## Standard File Patterns

### Cubit Pattern (Tier 1)

```dart
class FeatureCubit extends Cubit<FeatureState> {
  FeatureCubit(this._repository) : super(FeatureInitial());

  final FeatureRepository _repository;

  Future<void> load() async {
    emit(FeatureLoading());
    try {
      final data = await _repository.getData();
      emit(FeatureLoaded(data));
    } catch (e) {
      emit(FeatureError(e.toString()));
    }
  }
}
```

### BLoC Pattern (Tier 2)

```dart
@injectable
class FeatureBloc extends Bloc<FeatureEvent, FeatureState> {
  FeatureBloc(this._repository) : super(const FeatureState.loading()) {
    on<_Started>(_onStarted);
  }

  final FeatureRepository _repository;

  Future<void> _onStarted(_Started event, Emitter<FeatureState> emit) async {
    emit(const FeatureState.loading());
    try {
      final data = await _repository.getData();
      emit(FeatureState.success(data));
    } catch (e) {
      emit(FeatureState.error(e.toString()));
    }
  }
}
```

### Screen Pattern (All Tiers)

```dart
// Page — owns BlocProvider, never displays UI directly
class FeaturePage extends StatelessWidget {
  const FeaturePage({super.key});

  @override
  Widget build(BuildContext context) => BlocProvider(
    // Tier 1: pass repository from context or constructor
    // Tier 2: create: (_) => getIt<FeatureBloc>()..add(const FeatureEvent.started())
    create: (_) => FeatureCubit(context.read<FeatureRepository>())..load(),
    child: const FeatureScreen(),
  );
}

// Screen — pure UI, only reads from BlocBuilder
class FeatureScreen extends StatelessWidget {
  const FeatureScreen({super.key});

  @override
  Widget build(BuildContext context) => BlocBuilder<FeatureCubit, FeatureState>(
    builder: (context, state) => switch (state) {
      FeatureLoading() => const Center(child: CircularProgressIndicator()),
      FeatureLoaded(:final data) => ContentWidget(data: data),
      FeatureError(:final message) => ErrorWidget(message: message),
      FeatureInitial() => const SizedBox.shrink(),
    },
  );
}
```

### Side Effects with BlocListener

```dart
// Use BlocListener for one-time effects (navigation, snackbars, dialogs)
class FeaturePage extends StatelessWidget {
  const FeaturePage({super.key});

  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (_) => getIt<FeatureBloc>()..add(const FeatureEvent.started()),
    child: BlocListener<FeatureBloc, FeatureState>(
      listenWhen: (previous, current) => current is _Error,
      listener: (context, state) {
        if (state case _Error(:final message)) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(message)),
          );
        }
      },
      child: const FeatureScreen(),
    ),
  );
}
```

> Use `BlocConsumer` when the same widget needs both `BlocBuilder` (UI) and `BlocListener` (side effects).

---

## Key Dependencies

| Package | Tier 1 | Tier 2 | Purpose |
|---------|--------|--------|---------|
| flutter_bloc | ✅ | ✅ | BLoC/Cubit state management |
| go_router | ✅ | ✅ | Navigation |
| get_it | ✅ | ✅ | Service locator |
| injectable | ❌ | ✅ | Code-gen DI annotations |
| freezed | ❌ | ✅ | Immutable data classes + sealed states |
| freezed_annotation | ❌ | ✅ | freezed annotations |
| drift | optional | ✅ | Type-safe SQLite ORM |
| drift_flutter | optional | ✅ | Flutter drift integration |
| dio | optional | ✅ | HTTP client |
| shared_preferences | ✅ | optional | Simple key-value storage |
| build_runner | ❌ | ✅ | Code generation runner |
| injectable_generator | ❌ | ✅ | injectable code generator |
| drift_dev | ❌ | ✅ | Drift code generator |

## Flutter/Dart SDK Versions

| Setting | Value |
|---------|-------|
| Flutter SDK | 3.27.x+ |
| Dart SDK | 3.6.x+ |
| flutter_bloc | 9.1.x |
| go_router | 17.x |
| get_it | 9.x |
| injectable | 2.x |
| freezed | 2.x |
| drift | 2.x |
| dio | 5.x |

## Build Configuration

### Running Code Generation (Tier 2 Only)

```bash
# One-time build
dart run build_runner build --delete-conflicting-outputs

# Watch mode during development
dart run build_runner watch --delete-conflicting-outputs
```

Generated files to commit to version control:
- `injection.config.dart` — injectable output
- `*.g.dart` — go_router typed routes
- `*.freezed.dart` — freezed models
- `*.drift.dart` — Drift generated queries

Generated files to add to `.gitignore` — none. Commit all generated files. This avoids requiring all developers to run build_runner before building.

### Analysis Options

```yaml
# analysis_options.yaml
include: package:flutter_lints/flutter.yaml

analyzer:
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
    - "**/*.drift.dart"
    - "lib/injection.config.dart"
```
