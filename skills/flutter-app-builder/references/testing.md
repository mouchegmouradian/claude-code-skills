# Testing Reference

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Test Types](#test-types)
3. [Test Doubles (no mocking libraries)](#test-doubles-no-mocking-libraries)
4. [BLoC / Cubit Tests](#bloc--cubit-tests)
5. [Widget Tests (Page/Screen)](#widget-tests-pagescreen)
6. [Repository Tests](#repository-tests)
7. [Integration Tests](#integration-tests)
8. [Test Utilities](#test-utilities)

---

## Testing Philosophy

- **No mocking libraries** (mockito, mocktail) — use test doubles that implement interfaces
- Test doubles give more realistic behavior and catch interface drift
- BLoC test package (`bloc_test`) is the exception — it's a first-party testing utility, not a mock library
- Unit test BLoCs and Cubits directly — no widget tree needed
- Widget test Screens in isolation by passing plain state objects directly

---

## Test Types

| Type | What to test | Package |
|------|-------------|---------|
| Unit | BLoCs, Cubits, UseCases, Repositories | `flutter_test`, `bloc_test` |
| Widget | Screen widgets with injected state | `flutter_test` |
| Integration | Full feature flow with real dependencies | `integration_test` |

---

## Test Doubles

```dart
// Fake repository implementing the interface
class FakeItemRepository implements ItemRepository {
  final _items = <Item>[];
  bool syncCalled = false;

  void seed(List<Item> items) => _items
    ..clear()
    ..addAll(items);

  @override
  Stream<List<Item>> watchItems() => Stream.value(List.of(_items));

  @override
  Future<List<Item>> getItems() async => List.of(_items);

  @override
  Future<void> saveItem(Item item) async => _items.add(item);

  @override
  Future<void> deleteItem(String id) async => _items.removeWhere((i) => i.id == id);

  @override
  Future<void> sync() async => syncCalled = true;
}

// Fake streaming repository (for watch patterns)
class FakeStreamingItemRepository implements ItemRepository {
  final _controller = StreamController<List<Item>>.broadcast();

  void emit(List<Item> items) => _controller.add(items);

  @override
  Stream<List<Item>> watchItems() => _controller.stream;

  // ... other methods
}
```

---

## BLoC / Cubit Tests

### BLoC test

```dart
void main() {
  group('ItemBloc', () {
    late ItemBloc bloc;
    late FakeItemRepository repository;

    setUp(() {
      repository = FakeItemRepository();
      bloc = ItemBloc(GetItemsUseCase(repository));
    });

    tearDown(() => bloc.close());

    test('initial state is loading', () {
      expect(bloc.state, const ItemState.loading());
    });

    blocTest<ItemBloc, ItemState>(
      'emits success when items load',
      setUp: () => repository.seed([
        Item(id: '1', name: 'Item 1', createdAt: DateTime(2024)),
      ]),
      build: () => ItemBloc(GetItemsUseCase(repository)),
      act: (bloc) => bloc.add(const ItemEvent.started()),
      expect: () => [
        const ItemState.loading(),
        isA<_Success>().having((s) => s.items.length, 'items count', 1),
      ],
    );

    blocTest<ItemBloc, ItemState>(
      'emits error when repository throws',
      build: () {
        repository = ThrowingItemRepository();
        return ItemBloc(GetItemsUseCase(repository));
      },
      act: (bloc) => bloc.add(const ItemEvent.started()),
      expect: () => [
        const ItemState.loading(),
        isA<_Error>(),
      ],
    );
  });
}
```

### Cubit test (Tier 1 style — no freezed)

```dart
void main() {
  group('TodoCubit', () {
    late TodoCubit cubit;
    late FakeTodoRepository repository;

    setUp(() {
      repository = FakeTodoRepository();
      cubit = TodoCubit(repository);
    });
    tearDown(() => cubit.close());

    blocTest<TodoCubit, TodoState>(
      'loadTodos emits success with seeded items',
      setUp: () => repository.seed([Todo(id: '1', title: 'Test')]),
      build: () => TodoCubit(repository),
      act: (c) => c.loadTodos(),
      expect: () => [
        isA<TodoLoading>(),
        isA<TodoSuccess>().having((s) => s.todos.length, 'count', 1),
      ],
    );
  });
}
```

---

## Widget Tests (Page/Screen)

Test the Screen widget in isolation — inject state directly, no BLoC needed:

```dart
void main() {
  group('ItemScreen', () {
    testWidgets('shows loading indicator when loading', (tester) async {
      await tester.pumpWidget(
        BlocProvider<ItemBloc>.value(
          value: MockItemBloc()..stub(const ItemState.loading()),
          child: const MaterialApp(home: ItemScreen()),
        ),
      );
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('shows item list when success', (tester) async {
      final items = [Item(id: '1', name: 'Test Item', createdAt: DateTime(2024))];
      await tester.pumpWidget(
        BlocProvider<ItemBloc>.value(
          value: MockItemBloc()..stub(ItemState.success(items)),
          child: const MaterialApp(home: ItemScreen()),
        ),
      );
      expect(find.text('Test Item'), findsOneWidget);
    });
  });
}

// Minimal BLoC stub for widget tests (not a mock library)
class MockItemBloc extends MockBloc<ItemEvent, ItemState> implements ItemBloc {}
// Use bloc_test's MockBloc — this is acceptable (it's part of flutter_bloc ecosystem)
```

Alternative without MockBloc — pass state via a real BLoC seeded with initial state:

```dart
testWidgets('shows items', (tester) async {
  final bloc = ItemBloc(GetItemsUseCase(FakeItemRepository()..seed([...])));
  await tester.pumpWidget(
    BlocProvider.value(
      value: bloc..add(const ItemEvent.started()),
      child: const MaterialApp(home: ItemScreen()),
    ),
  );
  await tester.pump(); // let BLoC emit
  expect(find.text('Test Item'), findsOneWidget);
  bloc.close();
});
```

---

## Repository Tests

```dart
void main() {
  group('ItemRepositoryImpl', () {
    late ItemRepositoryImpl repository;
    late FakeItemDao dao;
    late FakeItemApiClient api;

    setUp(() {
      dao = FakeItemDao();
      api = FakeItemApiClient();
      repository = ItemRepositoryImpl(dao, api);
    });

    test('getItems returns mapped domain models from local DAO', () async {
      dao.seed([ItemsTableData(id: '1', name: 'Test', createdAt: DateTime(2024))]);
      final items = await repository.getItems();
      expect(items.length, 1);
      expect(items.first.name, 'Test');
    });

    test('sync fetches from network and upserts to DAO', () async {
      api.response = [ItemDto(id: '1', name: 'Remote', createdAt: '2024-01-01T00:00:00Z')];
      await repository.sync();
      expect(dao.upserted.length, 1);
    });
  });
}
```

---

## Integration Tests

Run full feature flows with real (or near-real) dependencies using `integration_test`:

```dart
// integration_test/items_flow_test.dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('items flow: load and display items', (tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();
    // Assert on real UI state driven by seeded or test-environment data
    expect(find.byType(ItemScreen), findsOneWidget);
  });
}
```

---

## Test Utilities

```dart
// test/helpers/pump_app.dart
extension PumpApp on WidgetTester {
  Future<void> pumpApp(Widget widget) => pumpWidget(
    MaterialApp(home: widget),
  );
}

// test/helpers/fake_repositories.dart
// Collect all fake implementations here for easy reuse across tests
```

### Running Tests

```bash
# All unit tests
flutter test

# Specific file
flutter test test/features/items/item_bloc_test.dart

# With coverage
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html

# Integration tests
flutter test integration_test/
```
