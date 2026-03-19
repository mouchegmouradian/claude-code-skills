# Dependency Injection Reference

## Table of Contents
1. [Overview](#overview)
2. [Tier 1 — Manual get_it](#tier-1--manual-get_it)
3. [Tier 2 — get_it + injectable](#tier-2--get_it--injectable)
4. [Injectable Annotations Reference](#injectable-annotations-reference)
5. [Scoping and Lifetime](#scoping-and-lifetime)
6. [Testing with get_it](#testing-with-get_it)

---

## Overview

Two-tier DI strategy:

- **Tier 1**: `get_it` service locator with manual registration in `main.dart`. No code generation. Simple and explicit.
- **Tier 2**: `get_it` + `injectable` with `@injectable`, `@lazySingleton`, `@singleton`, `@module` annotations. Code-gen via `build_runner`.

---

## Tier 1 — Manual get_it

```dart
// main.dart - register everything before runApp
final getIt = GetIt.instance;

void setupDependencies() {
  // Database / Preferences
  getIt.registerSingleton<SharedPreferences>(
    await SharedPreferences.getInstance(),
  );

  // Data sources
  getIt.registerLazySingleton<ItemRepository>(
    () => ItemRepository(getIt<SharedPreferences>()),
  );

  // BLoCs / Cubits are typically created per-page via BlocProvider
  // No need to register them in get_it for Tier 1
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  setupDependencies();
  runApp(const MyApp());
}
```

For Tier 1, BLoCs/Cubits are NOT registered in get_it. They are created directly in the Page widget via `BlocProvider`:

```dart
class ItemPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (_) => ItemCubit(getIt<ItemRepository>()),
    child: const ItemScreen(),
  );
}
```

---

## Tier 2 — get_it + injectable

### Setup

```dart
// lib/injection.dart
import 'injection.config.dart';

final getIt = GetIt.instance;

@InjectableInit(
  initializerName: 'init',
  preferRelativeImports: true,
  asExtension: true,
)
Future<void> configureDependencies() async => getIt.init();
```

```dart
// main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await configureDependencies();
  runApp(const MyApp());
}
```

Run code gen:

```bash
dart run build_runner build --delete-conflicting-outputs
```

### Annotated Repository

```dart
@LazySingleton(as: ItemRepository)
class ItemRepositoryImpl implements ItemRepository {
  ItemRepositoryImpl(this._dao, this._apiClient);
  final ItemDao _dao;
  final ItemApiClient _apiClient;
  // ...
}
```

### Annotated BLoC

```dart
@injectable
class ItemBloc extends Bloc<ItemEvent, ItemState> {
  ItemBloc(this._getItems) : super(const ItemState.loading()) {
    on<_Started>(_onStarted);
  }
  final GetItemsUseCase _getItems;
}
```

BLoCs use `@injectable` (not `@singleton`) — a new instance per page.

### Module for third-party types

```dart
@module
abstract class AppModule {
  @preResolve
  Future<SharedPreferences> get prefs => SharedPreferences.getInstance();

  @singleton
  AppDatabase get database => AppDatabase();

  @lazySingleton
  ItemDao itemDao(AppDatabase db) => db.itemDao;
}

@module
abstract class NetworkModule {
  @singleton
  Dio get dio => Dio(
    BaseOptions(baseUrl: Env.apiBaseUrl),
  )..interceptors.add(LogInterceptor());
}
```

### Page wiring (Tier 2)

```dart
class ItemPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (_) => getIt<ItemBloc>()..add(const ItemEvent.started()),
    child: const ItemScreen(),
  );
}
```

---

## Injectable Annotations Reference

| Annotation | Lifetime | Use Case |
|------------|----------|----------|
| `@singleton` | One instance, eager init | App-wide services |
| `@lazySingleton` | One instance, lazy init | Repositories, API clients |
| `@injectable` | New instance per request | BLoCs, Cubits, UseCases |
| `@module` | Declares external deps | Third-party libs (Dio, Drift, SharedPreferences) |
| `@preResolve` | Await async init | SharedPreferences, async setup |
| `@Named('foo')` | Named registration | Multiple implementations of same interface |

---

## Scoping and Lifetime

| Object | Registration | Reason |
|--------|-------------|--------|
| AppDatabase | `@singleton` | Single DB connection |
| Drift DAO | `@lazySingleton` | Wraps singleton DB |
| ItemRepository | `@LazySingleton(as: ItemRepository)` | Interface binding, lazy |
| Dio | `@singleton` | One HTTP client |
| ItemApiClient | `@lazySingleton` | Wraps singleton Dio |
| ItemBloc | `@injectable` | Per-page lifetime, disposed by BlocProvider |
| GetItemsUseCase | `@injectable` | Stateless, inject per use |

---

## Testing with get_it

For unit tests, bypass get_it entirely — inject fakes via constructor:

```dart
void main() {
  late ItemBloc bloc;
  late FakeItemRepository fakeRepo;

  setUp(() {
    fakeRepo = FakeItemRepository();
    final getItems = GetItemsUseCase(fakeRepo);
    bloc = ItemBloc(getItems);
  });

  tearDown(() => bloc.close());
}
```

For integration tests, reset and re-register get_it:

```dart
setUp(() async {
  await getIt.reset();
  getIt.registerLazySingleton<ItemRepository>(() => FakeItemRepository());
  getIt.registerFactory(() => ItemBloc(getIt<GetItemsUseCase>()));
});
```
