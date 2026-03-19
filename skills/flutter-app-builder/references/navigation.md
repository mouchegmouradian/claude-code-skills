# go_router Navigation Reference

Flutter SDK 3.27+ | Dart 3.6+ | go_router 17.x

---

## Table of Contents

1. [go_router Overview](#1-go_router-overview)
2. [Tier 1 — Basic Setup](#2-tier-1--basic-setup)
3. [Tier 2 — Type-Safe Routes](#3-tier-2--type-safe-routes)
4. [Route Guards (Redirects)](#4-route-guards-redirects)
5. [Navigation from BLoC / Outside Widget Tree](#5-navigation-from-bloc--outside-widget-tree)
6. [Nested Navigation](#6-nested-navigation)
7. [Navigation Patterns](#7-navigation-patterns)

---

## 1. go_router Overview

- Declarative, URL-based routing with deep link support
- Replaces `Navigator 2.0` boilerplate
- GoRouter lives in a singleton — Tier 1: manual global, Tier 2: injectable via get_it
- Supports type-safe routes via code generation (`go_router_builder`)
- Shell routes enable persistent bottom navigation

---

## 2. Tier 1 — Basic Setup

```dart
// router.dart
final GoRouter router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomePage(),
    ),
    GoRoute(
      path: '/items',
      builder: (context, state) => const ItemPage(),
      routes: [
        GoRoute(
          path: ':id',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return ItemDetailPage(id: id);
          },
        ),
      ],
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsPage(),
    ),
  ],
);

// app.dart
class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp.router(
    routerConfig: router,
    title: 'My App',
    theme: ThemeData(colorSchemeSeed: Colors.blue),
  );
}
```

Navigate: `context.go('/items')`, `context.push('/items/123')`, `context.pop()`

---

## 3. Tier 2 — Type-Safe Routes

Uses `go_router_builder` for compile-time safe navigation. Run `dart run build_runner build` to generate `.g.dart` files.

```dart
// router/routes.dart
part 'routes.g.dart';

@TypedGoRoute<HomeRoute>(path: '/')
class HomeRoute extends GoRouteData {
  const HomeRoute();
  @override
  Widget build(BuildContext context, GoRouterState state) => const HomePage();
}

@TypedGoRoute<ItemsRoute>(
  path: '/items',
  routes: [TypedGoRoute<ItemDetailRoute>(path: ':id')],
)
class ItemsRoute extends GoRouteData {
  const ItemsRoute();
  @override
  Widget build(BuildContext context, GoRouterState state) => const ItemsPage();
}

class ItemDetailRoute extends GoRouteData {
  const ItemDetailRoute({required this.id});
  final String id;
  @override
  Widget build(BuildContext context, GoRouterState state) => ItemDetailPage(id: id);
}

// Usage — type-safe navigation
const ItemDetailRoute(id: '123').go(context);
const ItemsRoute().push(context);
```

```dart
// router/app_router.dart
@singleton
class AppRouter {
  late final GoRouter config = GoRouter(
    initialLocation: '/',
    routes: $appRoutes,  // generated from @TypedGoRoute annotations
    redirect: _guard,
  );

  String? _guard(BuildContext context, GoRouterState state) {
    // auth guard logic
    return null;
  }
}

// injection
@module
abstract class RouterModule {
  @singleton
  AppRouter get appRouter => AppRouter();
}
```

---

## 4. Route Guards (Redirects)

### Basic auth guard

```dart
GoRouter(
  redirect: (context, state) {
    final isLoggedIn = context.read<AuthBloc>().state is _Authenticated;
    final isLoginRoute = state.matchedLocation == '/login';

    if (!isLoggedIn && !isLoginRoute) return '/login';
    if (isLoggedIn && isLoginRoute) return '/';
    return null; // no redirect
  },
)
```

### Tier 2 — reactive guard with stream refresh

```dart
GoRouter(
  refreshListenable: GoRouterRefreshStream(authBloc.stream),
  redirect: (context, state) { ... },
)

// Helper — bridges a Stream to ChangeNotifier for GoRouter
class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<dynamic> _subscription;
  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
```

---

## 5. Navigation from BLoC / Outside Widget Tree

In Tier 2, inject `AppRouter` via get_it and call directly. Useful for post-login redirects or error handling flows.

```dart
@injectable
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc(this._authRepository, this._appRouter) : super(...) { ... }
  final AppRouter _appRouter;

  void _onAuthenticated(...) {
    // Navigate from BLoC (outside widget tree)
    _appRouter.config.go('/home');
  }
}
```

Prefer `BlocListener` in the widget tree when possible — it is more testable and keeps navigation logic in the UI layer.

---

## 6. Nested Navigation

### Bottom Navigation / Shell Routes (Tier 2)

Shell routes keep the outer scaffold alive while swapping the inner navigator.

```dart
@TypedShellRoute<ShellRoute>(routes: [
  TypedGoRoute<HomeRoute>(path: '/'),
  TypedGoRoute<ItemsRoute>(path: '/items'),
  TypedGoRoute<ProfileRoute>(path: '/profile'),
])
class ShellRoute extends ShellRouteData {
  const ShellRoute();
  @override
  Widget builder(BuildContext context, GoRouterState state, Widget navigator) =>
    MainScaffold(child: navigator);
}
```

`MainScaffold` contains the `BottomNavigationBar` and renders `navigator` as its body. Each tab maintains its own navigation stack.

---

## 7. Navigation Patterns

| Pattern | Use When | Behavior |
|---------|----------|----------|
| `context.go()` | Navigate to a new top-level destination | Replaces entire history stack |
| `context.push()` | Drill into a detail screen | Preserves back button |
| `context.pop()` | Return to previous screen | Pops top of stack |
| `context.replace()` | Swap current screen without back entry | No history entry added |
| `context.goNamed()` | Navigate using route names | Avoids hardcoded path strings |
| `context.pushNamed()` | Push using route names | Same as push, name-based |

### Passing extra data (non-URL)

```dart
context.push('/detail', extra: myObject);

// Receive
final item = state.extra as MyObject;
```

Use `extra` for objects that should not appear in the URL. Avoid relying on `extra` for deep links since it is not serializable.
