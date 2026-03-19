# Flutter App Architecture Reference

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Data Layer](#2-data-layer)
3. [Domain Layer](#3-domain-layer)
4. [UI Layer](#4-ui-layer)
5. [Data Flow Example](#5-data-flow-example)

---

## 1. Architecture Overview

Flutter apps follow a **three-layer clean architecture** with unidirectional data flow.

- **Events flow DOWN**: UI → Domain → Data
- **Data flows UP**: Data → Domain → UI
- **Local Drift database is the source of truth** (Tier 2)

```
┌─────────────────────────────────────────┐
│                UI LAYER                 │
│  Pages · Screens · Widgets · BLoC/Cubit │
└──────────────────┬──────────────────────┘
                   │ events / calls
                   ▼
┌─────────────────────────────────────────┐
│              DOMAIN LAYER               │
│     UseCases (optional) · Models        │
│     Repository Interfaces               │
└──────────────────┬──────────────────────┘
                   │ calls
                   ▼
┌─────────────────────────────────────────┐
│               DATA LAYER                │
│  Repository Impls · DAOs · DTOs         │
│  Drift (SQLite) · Dio (network)         │
└─────────────────────────────────────────┘
```

| Concern | Tier 1 (Simple) | Tier 2 (Production) |
|---------|----------------|---------------------|
| State management | Cubit | BLoC or Cubit |
| DI | get_it (manual) | get_it + injectable |
| Models | Plain Dart sealed classes | freezed |
| Navigation | go_router | go_router |
| Local DB | Optional / Drift | Drift (source of truth) |
| Domain layer | Inline in Cubit | UseCases (when needed) |

---

## 2. Data Layer

### Principles
- **Offline-first** (Tier 2): local Drift database is always read first
- **Repository pattern**: abstract interface defined in domain, implementation in data
- **Reactive streams**: repositories expose `Stream<T>` so the UI reacts to changes automatically
- **Local-first**: remote data is fetched and persisted locally; UI only observes local state

### Repository Interface (Tier 2 — defined in domain layer)

```dart
abstract interface class ItemRepository {
  Stream<List<Item>> watchItems();
  Future<List<Item>> getItems();
  Future<void> saveItem(Item item);
  Future<void> deleteItem(String id);
  Future<void> sync();
}
```

### Repository Implementation

```dart
@LazySingleton(as: ItemRepository)
class ItemRepositoryImpl implements ItemRepository {
  ItemRepositoryImpl(this._localDataSource, this._remoteDataSource);
  final ItemLocalDataSource _localDataSource;
  final ItemRemoteDataSource _remoteDataSource;

  @override
  Stream<List<Item>> watchItems() => _localDataSource.watchAll().map(
    (entities) => entities.map((e) => e.toDomain()).toList(),
  );

  @override
  Future<List<Item>> getItems() async => _localDataSource.getAll().then(
    (entities) => entities.map((e) => e.toDomain()).toList(),
  );

  @override
  Future<void> sync() async {
    final dtos = await _remoteDataSource.fetchItems();
    await _localDataSource.upsertAll(dtos.map((dto) => dto.toEntity()).toList());
  }
}
```

### Data Sources

| Source | Technology | Purpose |
|--------|-----------|---------|
| Local | Drift DAO | Persistent SQLite storage, source of truth |
| Remote | Dio | HTTP API calls, returns DTOs |
| Preferences | SharedPreferences | Simple key-value storage (flags, tokens) |

### Drift DAO Pattern

```dart
@DriftAccessor(tables: [ItemTable])
class ItemDao extends DatabaseAccessor<AppDatabase> with _$ItemDaoMixin {
  ItemDao(super.db);

  Stream<List<ItemTableData>> watchAll() => select(itemTable).watch();
  Future<List<ItemTableData>> getAll() => select(itemTable).get();
  Future<void> upsertItem(ItemTableCompanion item) =>
      into(itemTable).insertOnConflictUpdate(item);
  Future<void> deleteItem(String id) =>
      (delete(itemTable)..where((t) => t.id.equals(id))).go();
}
```

### Model Mapping

Map between layers using Dart extensions — keep mapping logic close to the type being mapped.

```dart
// Entity → Domain model
extension ItemEntityMapper on ItemTableData {
  Item toDomain() => Item(id: id, name: name, createdAt: createdAt);
}

// DTO → Entity (for persistence after network fetch)
extension ItemDtoMapper on ItemDto {
  ItemTableCompanion toEntity() => ItemTableCompanion.insert(
    id: id,
    name: name,
    createdAt: DateTime.parse(createdAt),
  );
}
```

---

## 3. Domain Layer

### Purpose
- Encapsulate business logic that doesn't belong in the UI or data layer
- Combine data from multiple repositories
- Provide a stable API to the UI layer regardless of data source changes

### When to Add This Layer
The domain layer is **optional** — only add UseCases when:
- The same logic is reused across multiple BLoCs/Cubits
- Complex transformations or business rules are applied to raw data
- Data from multiple repositories must be combined

For simple CRUD flows in Tier 1, call the repository directly from the Cubit.

### UseCase Base Classes

```dart
abstract class UseCase<Type, Params> {
  Future<Type> call(Params params);
}

abstract class NoParamsUseCase<Type> {
  Future<Type> call();
}
```

### UseCase Example

```dart
@injectable
class GetItemsUseCase extends NoParamsUseCase<List<Item>> {
  GetItemsUseCase(this._repository);
  final ItemRepository _repository;

  @override
  Future<List<Item>> call() => _repository.getItems();
}
```

### When to Create a UseCase

| Scenario | Create UseCase? |
|----------|----------------|
| Simple repository pass-through | No — call repo directly |
| Logic reused across 2+ BLoCs | Yes |
| Combining data from 2+ repositories | Yes |
| Complex transformation / business rule | Yes |
| Tier 1 project | Rarely |

---

## 4. UI Layer

### Component Roles

| Component | Responsibility |
|-----------|---------------|
| **Page** | Composition root — wires DI via `BlocProvider`, owns the BLoC lifecycle |
| **Screen** | Pure UI — stateless, renders state via `BlocBuilder`, dispatches events |
| **Widget** | Reusable UI piece — no BLoC awareness |

Keeping Pages and Screens separate ensures Screens remain testable and reusable without DI setup.

### State Modeling with freezed (Tier 2)

```dart
@freezed
sealed class ItemState with _$ItemState {
  const factory ItemState.loading() = _Loading;
  const factory ItemState.success(List<Item> items) = _Success;
  const factory ItemState.error(String message) = _Error;
}
```

### BlocBuilder Pattern

```dart
class ItemScreen extends StatelessWidget {
  const ItemScreen({super.key});

  @override
  Widget build(BuildContext context) => BlocBuilder<ItemBloc, ItemState>(
    builder: (context, state) => state.when(
      loading: () => const CircularProgressIndicator(),
      success: (items) => ListView.builder(
        itemCount: items.length,
        itemBuilder: (_, i) => ListTile(title: Text(items[i].name)),
      ),
      error: (message) => Text(message),
    ),
  );
}
```

### BlocListener for Side Effects

Use `BlocListener` (not `BlocBuilder`) for one-time side effects that should not trigger a rebuild — navigation, snackbars, dialogs.

```dart
BlocListener<ItemBloc, ItemState>(
  listener: (context, state) {
    if (state is _Error) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.message)),
      );
    }
  },
)
```

---

## 5. Data Flow Example

Illustrates the full lifecycle from app startup to UI render using the offline-first pattern.

```
1. App startup
      │
      ▼
2. Page creates BlocProvider
   └─ BlocProvider(create: (_) => getIt<ItemBloc>()..add(const ItemEvent.started()))
      │
      ▼
3. BLoC emits Loading state
   └─ emit(const ItemState.loading())
      │
      ▼
4. BLoC calls UseCase (or Repository directly in Tier 1)
   └─ final items = await _getItemsUseCase()
      │
      ▼
5. UseCase calls Repository
   └─ return _repository.getItems()
      │
      ▼
6. Repository reads from Drift DAO
   └─ _localDataSource.getAll()
      │
      ▼
7. In background: BLoC also calls sync() to refresh from network
   └─ _repository.sync() → Dio fetch → upsert into Drift
      │
      ▼
8. Drift emits Stream<List<ItemTableData>> update
   └─ watchItems() stream fires with fresh data
      │
      ▼
9. Repository maps entity → domain model
   └─ entity.toDomain()
      │
      ▼
10. BLoC emits Success state
    └─ emit(ItemState.success(items))
       │
       ▼
11. Screen rebuilds via BlocBuilder
    └─ state.when(success: (items) => ListView(...))
```
