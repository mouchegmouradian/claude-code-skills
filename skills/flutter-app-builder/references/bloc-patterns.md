# BLoC / Cubit Patterns Reference

## Table of Contents
1. [Cubit vs BLoC Decision](#1-cubit-vs-bloc-decision)
2. [Cubit Patterns](#2-cubit-patterns)
3. [BLoC Patterns](#3-bloc-patterns)
4. [State Modeling](#4-state-modeling)
5. [Page / Screen Separation](#5-page--screen-separation)
6. [Side Effects with BlocListener](#6-side-effects-with-bloclistener)
7. [MultiBlocProvider](#7-multiblocprovider)
8. [BlocSelector for Granular Rebuilds](#8-blocselecto-for-granular-rebuilds)
9. [Common Patterns](#9-common-patterns)

---

## 1. Cubit vs BLoC Decision

| Use Cubit | Use BLoC |
|-----------|----------|
| Simple state mutations (toggle, counter, form) | Complex event-driven flows |
| No event history needed | Events need to be tracked or replayed |
| Tier 1 projects | Tier 2 projects with complex async flows |
| UI-driven state (loading, loaded, error) | Business event streams |

**Default to Cubit.** Upgrade to BLoC only when event complexity justifies it.

---

## 2. Cubit Patterns

### Basic Cubit (Tier 1 — no freezed)

Plain Dart sealed classes for state; manual get_it registration.

```dart
sealed class TodoState {}
class TodoInitial extends TodoState {}
class TodoLoading extends TodoState {}
class TodoSuccess extends TodoState {
  final List<Todo> todos;
  final bool isRefreshing;
  TodoSuccess({required this.todos, this.isRefreshing = false});
}
class TodoError extends TodoState {
  final String message;
  TodoError(this.message);
}

class TodoCubit extends Cubit<TodoState> {
  TodoCubit(this._repository) : super(TodoInitial());
  final TodoRepository _repository;

  Future<void> loadTodos() async {
    emit(TodoLoading());
    try {
      final todos = await _repository.getTodos();
      emit(TodoSuccess(todos: todos));
    } catch (e) {
      emit(TodoError(e.toString()));
    }
  }

  Future<void> addTodo(String title) async {
    final current = state;
    if (current is! TodoSuccess) return;
    final todo = Todo(id: uuid(), title: title);
    emit(TodoSuccess(todos: [...current.todos, todo]));
    await _repository.saveTodo(todo);
  }

  Future<void> deleteTodo(String id) async {
    final current = state;
    if (current is! TodoSuccess) return;
    emit(TodoSuccess(todos: current.todos.where((t) => t.id != id).toList()));
    await _repository.deleteTodo(id);
  }
}
```

> **Optimistic updates**: emit the new state immediately, then persist in the background. On error, re-emit the previous state or emit an error state.

### Cubit with freezed (Tier 2)

```dart
@freezed
sealed class TodoState with _$TodoState {
  const factory TodoState.initial() = _Initial;
  const factory TodoState.loading() = _Loading;
  const factory TodoState.success(
    List<Todo> todos, {
    @Default(false) bool isRefreshing,
  }) = _Success;
  const factory TodoState.error(String message) = _Error;
}

@injectable
class TodoCubit extends Cubit<TodoState> {
  TodoCubit(this._repository) : super(const TodoState.initial());
  final TodoRepository _repository;

  Future<void> loadTodos() async {
    emit(const TodoState.loading());
    try {
      final todos = await _repository.getTodos();
      emit(TodoState.success(todos));
    } catch (e) {
      emit(TodoState.error(e.toString()));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is! _Success) return;
    emit(TodoState.success(current.todos, isRefreshing: true));
    try {
      final todos = await _repository.getTodos();
      emit(TodoState.success(todos));
    } catch (e) {
      emit(TodoState.error(e.toString()));
    }
  }
}
```

---

## 3. BLoC Patterns

### Full BLoC with freezed Events + States (Tier 2)

Define events and states as freezed sealed classes. Register event handlers in the constructor.

```dart
// events
@freezed
sealed class AuthEvent with _$AuthEvent {
  const factory AuthEvent.loginRequested({
    required String email,
    required String password,
  }) = _LoginRequested;
  const factory AuthEvent.logoutRequested() = _LogoutRequested;
  const factory AuthEvent.sessionChecked() = _SessionChecked;
}

// state
@freezed
sealed class AuthState with _$AuthState {
  const factory AuthState.initial() = _Initial;
  const factory AuthState.loading() = _Loading;
  const factory AuthState.authenticated(User user) = _Authenticated;
  const factory AuthState.unauthenticated() = _Unauthenticated;
  const factory AuthState.error(String message) = _Error;
}

@injectable
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc(this._authRepository) : super(const AuthState.initial()) {
    on<_SessionChecked>(_onSessionChecked);
    on<_LoginRequested>(_onLoginRequested);
    on<_LogoutRequested>(_onLogoutRequested);
  }
  final AuthRepository _authRepository;

  Future<void> _onSessionChecked(
    _SessionChecked event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthState.loading());
    final user = await _authRepository.getSession();
    if (user != null) {
      emit(AuthState.authenticated(user));
    } else {
      emit(const AuthState.unauthenticated());
    }
  }

  Future<void> _onLoginRequested(
    _LoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthState.loading());
    try {
      final user = await _authRepository.login(event.email, event.password);
      emit(AuthState.authenticated(user));
    } catch (e) {
      emit(AuthState.error(e.toString()));
    }
  }

  Future<void> _onLogoutRequested(
    _LogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    await _authRepository.logout();
    emit(const AuthState.unauthenticated());
  }
}
```

---

## 4. State Modeling

### Tier 1 — Plain sealed classes

```dart
sealed class ScreenState {}
class ScreenInitial extends ScreenState {}
class ScreenLoading extends ScreenState {}
class ScreenSuccess extends ScreenState {
  final List<Item> items;
  ScreenSuccess(this.items);
}
class ScreenError extends ScreenState {
  final String message;
  ScreenError(this.message);
}
```

### Tier 2 — freezed sealed classes

```dart
@freezed
sealed class ScreenState with _$ScreenState {
  const factory ScreenState.initial() = _Initial;
  const factory ScreenState.loading() = _Loading;
  const factory ScreenState.success(List<Item> items) = _Success;
  const factory ScreenState.error(String message) = _Error;
}
```

### Choosing a State Shape

| Scenario | Recommendation |
|----------|---------------|
| Mutually exclusive states (loading / success / error) | Sealed classes (union type) |
| Shared fields across states (e.g., always show list while refreshing) | Single data class with status field |
| Complex form with many independent fields | Single state class with `copyWith` |

---

## 5. Page / Screen Separation

The **Page** is the composition root. It is responsible for creating and providing the BLoC via `BlocProvider`. The **Screen** is a pure stateless widget that renders state and dispatches events — it has no knowledge of DI.

This separation keeps Screens independently testable and reusable.

### Tier 1 — Manual get_it

```dart
// item_page.dart
class ItemPage extends StatelessWidget {
  const ItemPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ItemCubit(getIt<ItemRepository>())..loadItems(),
      child: const ItemScreen(),
    );
  }
}

// item_screen.dart
class ItemScreen extends StatelessWidget {
  const ItemScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ItemCubit, ItemState>(
      builder: (context, state) {
        // render state
      },
    );
  }
}
```

### Tier 2 — injectable + get_it

```dart
// item_page.dart
class ItemPage extends StatelessWidget {
  const ItemPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<ItemBloc>()..add(const ItemEvent.started()),
      child: const ItemScreen(),
    );
  }
}
```

---

## 6. Side Effects with BlocListener

| Widget | When to use |
|--------|-------------|
| `BlocBuilder` | Rebuild UI in response to state changes |
| `BlocListener` | One-time side effects: navigation, snackbars, dialogs |
| `BlocConsumer` | Both — rebuild UI and trigger side effects from the same state |

### BlocConsumer Example

```dart
BlocConsumer<AuthBloc, AuthState>(
  listener: (context, state) {
    if (state is _Authenticated) context.go('/home');
    if (state is _Error) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.message)),
      );
    }
  },
  builder: (context, state) => state.when(
    initial: () => const SizedBox(),
    loading: () => const CircularProgressIndicator(),
    authenticated: (_) => const SizedBox(),
    unauthenticated: () => const LoginForm(),
    error: (msg) => Text(msg),
  ),
)
```

### listenWhen / buildWhen

Use these to limit when the listener or builder fires — useful for avoiding double-triggers.

```dart
BlocConsumer<AuthBloc, AuthState>(
  listenWhen: (previous, current) => current is _Authenticated || current is _Error,
  buildWhen: (previous, current) => current is! _Error,
  listener: (context, state) { /* ... */ },
  builder: (context, state) { /* ... */ },
)
```

---

## 7. MultiBlocProvider

Flatten nested `BlocProvider`s at the app or route level with `MultiBlocProvider`.

```dart
MultiBlocProvider(
  providers: [
    BlocProvider(
      create: (_) => getIt<AuthBloc>()..add(const AuthEvent.sessionChecked()),
    ),
    BlocProvider(
      create: (_) => getIt<ThemeCubit>(),
    ),
  ],
  child: const AppView(),
)
```

> Place `MultiBlocProvider` above `MaterialApp` only for truly global state (auth, theme). Prefer scoping BLoCs to the route or page that needs them.

---

## 8. BlocSelector for Granular Rebuilds

`BlocSelector` rebuilds only when the selected value changes, preventing unnecessary rebuilds when unrelated parts of state update.

```dart
BlocSelector<ItemBloc, ItemState, int>(
  selector: (state) => state.maybeWhen(
    success: (items) => items.length,
    orElse: () => 0,
  ),
  builder: (context, count) => Text('$count items'),
)
```

Use `BlocSelector` when:
- The widget only cares about one field of a large state object
- You want to optimize rebuild performance in lists or complex screens

---

## 9. Common Patterns

### Stream subscription in BLoC

Use `emit.forEach` (or `emit.onEach`) to subscribe to a `Stream` from a repository and emit a new state for each event.

```dart
Future<void> _onStarted(_Started event, Emitter<ItemState> emit) async {
  await emit.forEach<List<Item>>(
    _repository.watchItems(),
    onData: (items) => ItemState.success(items),
    onError: (_, __) => const ItemState.error('Failed to load items'),
  );
}
```

### Triggering BLoC event on page load

Fire an initial event inside `BlocProvider.create` so the BLoC starts loading as soon as it is created.

```dart
BlocProvider(
  create: (_) => getIt<ItemBloc>()..add(const ItemEvent.started()),
  child: const ItemScreen(),
)
```

### Accessing BLoC from a widget

```dart
// Read (dispatch event, no rebuild)
context.read<ItemBloc>().add(const ItemEvent.refresh());

// Watch (rebuilds on every state change — use inside build only)
final state = context.watch<ItemCubit>().state;

// Select (rebuilds only when selected value changes)
final count = context.select<ItemCubit, int>(
  (cubit) => cubit.state is TodoSuccess ? (cubit.state as TodoSuccess).todos.length : 0,
);
```

### Error recovery

Always provide a way for the user to retry after an error state.

```dart
error: (message) => Column(
  children: [
    Text(message),
    ElevatedButton(
      onPressed: () => context.read<ItemBloc>().add(const ItemEvent.started()),
      child: const Text('Retry'),
    ),
  ],
),
```
