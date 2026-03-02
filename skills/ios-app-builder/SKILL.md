---
name: ios-app-builder
description: Create production-quality iOS applications following Apple's official guidance and modern Swift patterns. Use when building iOS apps with Swift, SwiftUI, MVVM, Swift Concurrency (actors, async/await), SwiftData, or multi-module projects. Triggers on requests to create iOS projects, screens, ViewModels, repositories, feature modules, actors, or iOS architecture patterns.
---

# iOS Development

Build iOS applications following Apple's official architecture guidance, modern Swift concurrency patterns, and SwiftUI best practices.

## Quick Reference

| Task | Reference File |
|------|----------------|
| Architecture layers (UI, Domain, Data) | [architecture.md](references/architecture.md) |
| SwiftUI patterns & navigation | [swiftui-patterns.md](references/swiftui-patterns.md) |
| Swift Actors & concurrency | [actors.md](references/actors.md) |
| Project & build configuration | [project-setup.md](references/project-setup.md) |
| Project structure & modules | [modularization.md](references/modularization.md) |
| Testing approach | [testing.md](references/testing.md) |

## Workflow Decision Tree

**Creating a new project?**
→ Read [project-setup.md](references/project-setup.md) for SPM and Xcode setup
→ Read [modularization.md](references/modularization.md) for module structure
→ Use templates in `assets/templates/`

**Adding a new feature?**
→ Create feature module following [modularization.md](references/modularization.md)
→ Follow patterns in [architecture.md](references/architecture.md)

**Building UI screens?**
→ Read [swiftui-patterns.md](references/swiftui-patterns.md)
→ Create Route + Screen + ViewModel

**Setting up data layer?**
→ Read data layer section in [architecture.md](references/architecture.md)
→ Create Repository protocol + actor implementation + @ModelActor

**Working with concurrency?**
→ Read [actors.md](references/actors.md) for actors, Sendable, async/await
→ Follow the actor decision tree

**Writing tests?**
→ Read [testing.md](references/testing.md)
→ Use Swift Testing framework with protocol-based test doubles

## Core Principles

1. **Offline-first**: Local persistence (SwiftData) is source of truth, sync with remote
2. **Unidirectional data flow**: Events flow down, data flows up
3. **Reactive streams**: Use AsyncSequence/AsyncStream for all data exposure
4. **Modular by feature**: Each feature is self-contained via Swift Package modules
5. **Testable by design**: Use protocols and test doubles, no mocking libraries
6. **Actor-isolated concurrency**: Use actors for shared mutable state, @MainActor for UI

## Architecture Layers

```
┌─────────────────────────────────────────┐
│              UI Layer                    │
│  (SwiftUI Views + @Observable VMs)      │
├─────────────────────────────────────────┤
│           Domain Layer                   │
│  (Use Cases - optional, for reuse)       │
├─────────────────────────────────────────┤
│            Data Layer                    │
│  (Repositories + DataSources)            │
└─────────────────────────────────────────┘
```

## Module Types

```
App/                        # App target - entry point, navigation, @main
Features/
  ├── FeatureName/
  │   ├── Sources/          # Route, Screen, ViewModel
  │   └── Tests/            # Feature tests
Core/
  ├── Model/                # Domain models (pure Swift structs)
  ├── Data/                 # Repositories (protocols + actor implementations)
  ├── Database/             # SwiftData models, @ModelActor
  ├── Network/              # URLSession, API models, DTOs
  ├── Common/               # Shared utilities, extensions
  ├── UI/                   # Reusable SwiftUI components
  ├── DesignSystem/         # Theme, colors, typography, SF Symbols
  └── Testing/              # Test utilities, test doubles
```

## Creating a New Feature

1. Create feature module in `Features/MyFeature/`
2. Add target to `Package.swift` with dependencies on Core modules
3. Create these files:
   - `MyFeatureRoute.swift` - Owns ViewModel (`@State`), handles navigation
   - `MyFeatureScreen.swift` - Receives ViewModel (`let`), renders UI
   - `MyFeatureViewModel.swift` - @MainActor @Observable with individual properties

## Standard File Patterns

### ViewModel Pattern

Expose individual properties — SwiftUI's `@Observable` tracks each property accessed per view, enabling granular re-renders. Avoid wrapping state in a single enum (that forces full re-renders).

```swift
@MainActor
@Observable
final class MyFeatureViewModel {
    private(set) var items: [Item] = []
    private(set) var isLoading = false
    var errorMessage: String?

    private let repository: MyRepository

    init(repository: MyRepository) {
        self.repository = repository
    }

    func onAppear() async {
        isLoading = true
        defer { isLoading = false }
        do {
            items = try await repository.getItems()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func deleteItem(id: String) async {
        do {
            try await repository.deleteItem(id: id)
            items.removeAll { $0.id == id }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func refresh() async {
        await onAppear()
    }
}
```

### Screen Pattern (Route/Screen Separation)

- **Route** creates and owns the ViewModel with `@State`
- **Screen** receives the ViewModel as `let` — no wrapper needed, SwiftUI auto-tracks `@Observable`
- For two-way bindings (TextField, Toggle), use `@Bindable` locally in the body

```swift
// Route: owns ViewModel via @State, connects navigation
struct MyFeatureRoute: View {
    @State private var viewModel: MyFeatureViewModel

    init(repository: MyRepository) {
        viewModel = MyFeatureViewModel(repository: repository)
    }

    var body: some View {
        MyFeatureScreen(viewModel: viewModel)
            .task { await viewModel.onAppear() }
            .refreshable { await viewModel.refresh() }
            .navigationTitle("My Feature")
    }
}

// Screen: receives ViewModel, reads properties directly
struct MyFeatureScreen: View {
    let viewModel: MyFeatureViewModel

    var body: some View {
        List(viewModel.items) { item in
            Text(item.name)
                .swipeActions {
                    Button("Delete", role: .destructive) {
                        Task { await viewModel.deleteItem(id: item.id) }
                    }
                }
        }
        .overlay {
            if viewModel.isLoading && viewModel.items.isEmpty {
                ProgressView()
            }
        }
        .overlay {
            if let error = viewModel.errorMessage, viewModel.items.isEmpty {
                ContentUnavailableView(
                    "Error",
                    systemImage: "exclamationmark.triangle",
                    description: Text(error)
                )
            }
        }
    }
}
```

> **When to use a state enum instead**: Use `enum UiState` only for truly mutually exclusive states like onboarding flows (`step1 | step2 | step3`) or auth state (`loggedIn | loggedOut`), where you cannot show content and loading simultaneously.

### Property Wrapper Decision (WWDC 2023)

| View role | Wrapper | Example |
|-----------|---------|---------|
| Creates the ViewModel | `@State` | `@State private var viewModel = MyVM()` |
| Receives from parent | `let` (none) | `let viewModel: MyVM` |
| Needs `$` bindings | `@Bindable` | `@Bindable var viewModel = viewModel` |
| Shared app-wide | `@Environment` | `@Environment(AppState.self) var appState` |

### Repository Pattern
```swift
// Protocol: defines contract, Sendable for cross-isolation use
protocol MyRepository: Sendable {
    func getItems() async throws -> [MyModel]
    func observeItems() -> AsyncStream<[MyModel]>
    func updateItem(_ item: MyModel) async throws
    func sync() async throws
}

// Implementation: actor for thread-safe shared state
actor OfflineFirstMyRepository: MyRepository {
    private let persistence: MyPersistenceActor
    private let network: NetworkClient

    init(persistence: MyPersistenceActor, network: NetworkClient) {
        self.persistence = persistence
        self.network = network
    }

    func getItems() async throws -> [MyModel] {
        try await persistence.fetchAll()
    }

    func observeItems() -> AsyncStream<[MyModel]> {
        persistence.observeAll()
    }

    func updateItem(_ item: MyModel) async throws {
        try await persistence.upsert(item)
    }

    func sync() async throws {
        let remoteItems = try await network.fetchItems()
        for item in remoteItems {
            try await persistence.upsert(item.toDomainModel())
        }
    }
}
```

## Key Dependencies

```
Swift 6+ (strict concurrency)
iOS 17+ (required for @Observable, SwiftData, #Preview)
SwiftData (persistence)
Swift Testing (unit tests)
XCTest (UI tests)
```

## Build Configuration

Use Swift Package Manager for multi-module projects:
- Local package inside Xcode workspace
- Each feature and core module is a separate target
- Strict concurrency checking enabled (`-strict-concurrency=complete`)
- Swift 6 language mode

See [project-setup.md](references/project-setup.md) for complete configuration.
