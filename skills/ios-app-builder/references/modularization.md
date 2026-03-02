# Modularization

Multi-module project structure using Swift Package Manager. Each module has clear boundaries, explicit dependencies, and proper access control.

---

## Why Modularize

| Benefit | Description |
|---------|-------------|
| **Build speed** | Only recompile changed modules |
| **Encapsulation** | `internal` by default hides implementation |
| **Parallel development** | Teams work on isolated modules |
| **Testability** | Test modules in isolation with focused dependencies |
| **Reusability** | Core modules can be shared across targets/apps |
| **Compile-time safety** | Dependency violations are compile errors |

---

## Module Types

### App Target

Entry point. Owns `@main`, root navigation, and dependency composition.

```
App/
├── MyApp.swift              # @main, composition root
├── Navigation/
│   ├── AppNavigation.swift  # Root NavigationStack, route handling
│   └── AppRoute.swift       # Route enum
└── Assets.xcassets
```

The app target imports **all feature modules** and **core modules it needs** to compose the dependency graph.

### Feature Modules

Self-contained features. Each has its own Route, Screen, and ViewModel.

```
Sources/FeatureHome/
├── HomeRoute.swift           # Route (owns ViewModel via @State, lifecycle)
├── HomeScreen.swift          # Screen (receives ViewModel as let, renders UI)
├── HomeViewModel.swift       # @MainActor @Observable with individual properties
└── Components/               # Feature-local UI components
    ├── TopicCard.swift
    └── FeaturedBanner.swift
```

**Feature modules depend on Core modules, never on other Feature modules.**

### Core Modules

Shared infrastructure and domain logic.

| Module | Purpose | Dependencies |
|--------|---------|-------------|
| `CoreModel` | Domain models (pure Swift structs) | None |
| `CoreData` | Repository protocols + actor implementations | CoreModel, CoreDatabase, CoreNetwork |
| `CoreDatabase` | SwiftData @Model entities, @ModelActor | CoreModel |
| `CoreNetwork` | URLSession client, DTOs, network errors | CoreModel |
| `CoreCommon` | Extensions, utilities, formatters | CoreModel |
| `CoreUI` | Reusable SwiftUI components | CoreModel, CoreDesignSystem |
| `CoreDesignSystem` | Theme, colors, typography, SF Symbols | None |
| `CoreTesting` | Test doubles, sample data factories | CoreModel, CoreData |

---

## Dependency Rules

```
App → Feature:* → Core:Data → Core:Database
                             → Core:Network
                             → Core:Model
    → Feature:* → Core:UI   → Core:DesignSystem
                             → Core:Model
    → Feature:* → Core:Common → Core:Model
```

### Forbidden Dependencies

| From | To | Why |
|------|----|-----|
| Feature A | Feature B | Features are isolated; communicate through App navigation |
| Core | Feature | Core is foundational; features depend on it, not vice versa |
| CoreModel | Anything | Domain models are pure Swift, zero dependencies |
| CoreDesignSystem | Anything | Design tokens are standalone |

### Module Dependency Graph

```
                        ┌─────────┐
                        │   App   │
                        └────┬────┘
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
          ┌────────────┐ ┌────────────┐ ┌────────────┐
          │FeatureHome │ │FeatureList │ │FeatureUser │
          └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
                │              │              │
        ┌───────┴──────────────┴──────────────┘
        ▼           ▼           ▼           ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
  │CoreData  │ │ CoreUI   │ │CoreCommon│ │CoreModel │
  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────┘
       │             │            │              ▲
       ▼             ▼            │              │
  ┌──────────┐ ┌───────────┐     └──────────────┘
  │CoreDB    │ │CoreDesign │
  │CoreNet   │ │System     │
  └──────────┘ └───────────┘
```

---

## Access Control

### Swift Access Levels in SPM

| Level | Visibility | Use For |
|-------|-----------|---------|
| `public` | Any importing module | Module API: protocols, models, view factories |
| `package` | Same Swift package | Cross-module within AppModules, not exposed to App |
| `internal` (default) | Same module only | Implementation details |
| `private` / `fileprivate` | Same file/scope | Private helpers |

### What to Make Public

```swift
// CoreModel — public domain models
public struct Topic: Identifiable, Equatable, Sendable {
    public let id: String
    public var name: String
    public var description: String

    public init(id: String, name: String, description: String) {
        self.id = id
        self.name = name
        self.description = description
    }
}

// CoreData — public protocol, internal implementation
public protocol TopicRepository: Sendable {
    func getTopics() async throws -> [Topic]
    func sync() async throws
}

// Implementation is internal (or package) — callers use the protocol
actor OfflineFirstTopicRepository: TopicRepository {
    // ...
}

// Public factory for dependency composition
public func makeTopicRepository(container: ModelContainer) -> TopicRepository {
    let persistence = TopicPersistence(modelContainer: container)
    let network = TopicNetworkClient(baseURL: apiBaseURL)
    return OfflineFirstTopicRepository(persistence: persistence, network: network)
}
```

### Feature Module Exports

```swift
// FeatureHome — only export the Route (entry point)
public struct HomeRoute: View {
    public init(repository: TopicRepository, onNavigateToDetail: @escaping (String) -> Void) {
        // ...
    }

    public var body: some View {
        // ...
    }
}

// Screen and ViewModel are internal — not visible outside the module
struct HomeScreen: View { /* ... */ }

@MainActor @Observable
final class HomeViewModel { /* ... */ }
```

---

## Adding a New Feature Module

1. Create directory: `Sources/FeatureMyFeature/`
2. Create files: Route, Screen, ViewModel
3. Add target to `Package.swift`:

```swift
.target(
    name: "FeatureMyFeature",
    dependencies: [
        "CoreData",
        "CoreUI",
    ]
),
.testTarget(
    name: "FeatureMyFeatureTests",
    dependencies: ["FeatureMyFeature", "CoreTesting"]
),
```

4. Add product to `Package.swift` products array:

```swift
.library(name: "FeatureMyFeature", targets: ["FeatureMyFeature"]),
```

5. Import in App target and add to navigation.

Or use `scripts/generate_feature.py` to automate steps 1-2.

---

## Adding a New Core Module

1. Create directory: `Sources/CoreMyModule/`
2. Add target with appropriate dependencies
3. Add product to products array
4. Update dependent modules to import it

**Rule**: Core modules should have the minimum dependencies possible. `CoreModel` depends on nothing.
