# Data Layer Reference

Flutter SDK 3.27+ | Dart 3.6+ | drift 2.x | dio 5.x

---

## Table of Contents

1. [Overview](#1-overview)
2. [Repository Pattern](#2-repository-pattern)
3. [Drift (Local Database)](#3-drift-local-database)
4. [Dio (Network)](#4-dio-network)
5. [Model Mapping](#5-model-mapping)
6. [Offline-First Sync](#6-offline-first-sync)
7. [SharedPreferences (Tier 1)](#7-sharedpreferences-tier-1)

---

## 1. Overview

- Two data sources: local (Drift/SQLite) and remote (Dio/HTTP)
- Repository is the single public API for data — BLoC/Cubit never touches DAO or API client directly
- Local database is the source of truth (Tier 2 offline-first pattern)
- Data flow: `Remote DTO → Database Entity → Domain Model`

### Tier comparison

| Concern | Tier 1 (Simple) | Tier 2 (Production) |
|---------|----------------|---------------------|
| Models | Plain Dart classes | freezed |
| DI | get_it (manual) | get_it + injectable |
| Local storage | SharedPreferences | Drift (SQLite) |
| Sync | None | Offline-first via SyncService |
| DTOs | `fromJson` manual | freezed + json_serializable |

---

## 2. Repository Pattern

### Abstract interface (domain layer)

```dart
// domain/repositories/item_repository.dart
abstract interface class ItemRepository {
  Stream<List<Item>> watchItems();
  Future<List<Item>> getItems();
  Future<void> saveItem(Item item);
  Future<void> deleteItem(String id);
  Future<void> sync();
}
```

### Implementation (data layer — full Tier 2 example)

```dart
// data/repositories/item_repository_impl.dart
@LazySingleton(as: ItemRepository)
class ItemRepositoryImpl implements ItemRepository {
  ItemRepositoryImpl(this._dao, this._apiClient);
  final ItemDao _dao;
  final ItemApiClient _apiClient;

  @override
  Stream<List<Item>> watchItems() => _dao.watchAll().map(
    (rows) => rows.map((r) => r.toDomain()).toList(),
  );

  @override
  Future<List<Item>> getItems() async {
    final rows = await _dao.getAll();
    return rows.map((r) => r.toDomain()).toList();
  }

  @override
  Future<void> saveItem(Item item) => _dao.upsert(item.toEntity());

  @override
  Future<void> deleteItem(String id) => _dao.delete(id);

  @override
  Future<void> sync() async {
    final dtos = await _apiClient.getItems();
    await _dao.upsertAll(dtos.map((dto) => dto.toEntity()).toList());
  }
}
```

---

## 3. Drift (Local Database)

### Database setup

```dart
// data/local/app_database.dart
@DriftDatabase(tables: [ItemsTable], daos: [ItemDao])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (m) => m.createAll(),
    onUpgrade: (m, from, to) async {
      // handle migrations per version step
    },
  );
}

LazyDatabase _openConnection() => LazyDatabase(() async {
  final dbFolder = await getApplicationDocumentsDirectory();
  final file = File(path.join(dbFolder.path, 'app.db'));
  return NativeDatabase.createInBackground(file);
});

// Register in get_it
@module
abstract class DatabaseModule {
  @singleton
  AppDatabase get database => AppDatabase();
}
```

### Table definition

```dart
// data/local/tables/items_table.dart
class ItemsTable extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}
```

Add nullable columns with `.nullable()`, set defaults with `.withDefault(const Constant(...))`.

### DAO

```dart
// data/local/daos/item_dao.dart
@DriftAccessor(tables: [ItemsTable])
class ItemDao extends DatabaseAccessor<AppDatabase> with _$ItemDaoMixin {
  ItemDao(super.db);

  Stream<List<ItemsTableData>> watchAll() => select(itemsTable).watch();
  Future<List<ItemsTableData>> getAll() => select(itemsTable).get();

  Future<void> upsert(ItemsTableCompanion item) =>
    into(itemsTable).insertOnConflictUpdate(item);

  Future<void> upsertAll(List<ItemsTableCompanion> items) =>
    batch((b) => b.insertAllOnConflictUpdate(itemsTable, items));

  Future<void> delete(String id) =>
    (deleteStatement(itemsTable)..where((t) => t.id.equals(id))).go();
}
```

### Querying with filters

```dart
Future<List<ItemsTableData>> getByName(String name) =>
  (select(itemsTable)..where((t) => t.name.like('%$name%'))).get();
```

### Migrations

Increment `schemaVersion` and handle each version transition in `onUpgrade`:

```dart
onUpgrade: (m, from, to) async {
  if (from < 2) {
    await m.addColumn(itemsTable, itemsTable.someNewColumn);
  }
},
```

---

## 4. Dio (Network)

### Client setup with interceptors

```dart
// data/remote/dio_client.dart
@module
abstract class NetworkModule {
  @singleton
  Dio get dio {
    final dio = Dio(
      BaseOptions(
        baseUrl: const String.fromEnvironment('API_BASE_URL'),
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );
    dio.interceptors.addAll([
      LogInterceptor(requestBody: true, responseBody: true),
      AuthInterceptor(),
    ]);
    return dio;
  }
}

class AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['Authorization'] = 'Bearer ${getIt<TokenStore>().token}';
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      // Handle token refresh or logout
    }
    handler.next(err);
  }
}
```

### API client

```dart
// data/remote/item_api_client.dart
@lazySingleton
class ItemApiClient {
  ItemApiClient(this._dio);
  final Dio _dio;

  Future<List<ItemDto>> getItems() async {
    final response = await _dio.get<List<dynamic>>('/items');
    return response.data!
      .map((json) => ItemDto.fromJson(json as Map<String, dynamic>))
      .toList();
  }

  Future<ItemDto> getItem(String id) async {
    final response = await _dio.get<Map<String, dynamic>>('/items/$id');
    return ItemDto.fromJson(response.data!);
  }

  Future<void> deleteItem(String id) => _dio.delete('/items/$id');
}
```

### DTO with freezed (Tier 2)

```dart
@freezed
class ItemDto with _$ItemDto {
  const factory ItemDto({
    required String id,
    required String name,
    @JsonKey(name: 'created_at') required String createdAt,
  }) = _ItemDto;

  factory ItemDto.fromJson(Map<String, dynamic> json) => _$ItemDtoFromJson(json);
}
```

### DTO without freezed (Tier 1)

```dart
class ItemDto {
  const ItemDto({required this.id, required this.name, required this.createdAt});

  final String id;
  final String name;
  final String createdAt;

  factory ItemDto.fromJson(Map<String, dynamic> json) => ItemDto(
    id: json['id'] as String,
    name: json['name'] as String,
    createdAt: json['created_at'] as String,
  );
}
```

---

## 5. Model Mapping

Keep mapping logic in extension methods close to the source type. Never map inside the repository — use dedicated mapper extensions.

```dart
// Entity → Domain
extension ItemEntityMapper on ItemsTableData {
  Item toDomain() => Item(id: id, name: name, createdAt: createdAt);
}

// DTO → Entity (for persisting remote data)
extension ItemDtoMapper on ItemDto {
  ItemsTableCompanion toEntity() => ItemsTableCompanion.insert(
    id: id,
    name: name,
    createdAt: DateTime.parse(createdAt),
  );
}

// Domain → Entity (for local saves)
extension ItemDomainMapper on Item {
  ItemsTableCompanion toEntity() => ItemsTableCompanion.insert(
    id: id,
    name: name,
    createdAt: createdAt,
  );
}
```

---

## 6. Offline-First Sync

### SyncService

```dart
// data/services/sync_service.dart
@injectable
class SyncService {
  SyncService(this._itemRepository, this._connectivityService);
  final ItemRepository _itemRepository;
  final ConnectivityService _connectivityService;

  Future<void> syncAll() async {
    if (!await _connectivityService.isConnected) return;
    await _itemRepository.sync();
  }
}
```

Call from app startup or trigger on connectivity-restored events.

### Connectivity service

```dart
@lazySingleton
class ConnectivityService {
  Future<bool> get isConnected async {
    final result = await Connectivity().checkConnectivity();
    return result != ConnectivityResult.none;
  }
}
```

### Pattern summary

1. UI always reads from Drift via `watchItems()` stream — reactive, no manual refresh
2. On app start or reconnect, `SyncService.syncAll()` fetches remote data and upserts locally
3. Write operations update local DB immediately (optimistic), then sync to remote
4. Conflict resolution strategy: last-write-wins via `insertOnConflictUpdate`

---

## 7. SharedPreferences (Tier 1)

Use for small, non-relational key-value data (theme, onboarding flags, user preferences).

```dart
// data/repositories/preferences_repository.dart
class PreferencesRepository {
  PreferencesRepository(this._prefs);
  final SharedPreferences _prefs;

  static const _themeKey = 'theme_mode';

  ThemeMode get themeMode {
    final value = _prefs.getString(_themeKey);
    return ThemeMode.values.firstWhere(
      (e) => e.name == value,
      orElse: () => ThemeMode.system,
    );
  }

  Future<void> setThemeMode(ThemeMode mode) =>
    _prefs.setString(_themeKey, mode.name);
}

// Register in get_it
@module
abstract class PreferencesModule {
  @preResolve
  Future<SharedPreferences> get sharedPreferences => SharedPreferences.getInstance();
}
```

`@preResolve` tells injectable to await the future during `configureDependencies()` so the instance is available synchronously after setup.
