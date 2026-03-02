# Project Setup

Swift Package Manager configuration, Xcode workspace structure, and build settings for multi-module iOS projects.

---

## Project Structure

```
MyApp/
├── MyApp.xcodeproj              # Xcode project (App target only)
├── MyApp/                       # App target sources
│   ├── MyApp.swift              # @main entry point
│   ├── ContentView.swift        # Root view
│   ├── Navigation/              # App navigation
│   └── Assets.xcassets          # App assets
├── AppModules/                  # Local SPM package (all modules)
│   ├── Package.swift            # Module definitions
│   ├── Sources/
│   │   ├── CoreModel/           # Domain models
│   │   ├── CoreData/            # Repositories
│   │   ├── CoreDatabase/        # SwiftData persistence
│   │   ├── CoreNetwork/         # URLSession networking
│   │   ├── CoreUI/              # Reusable components
│   │   ├── CoreDesignSystem/    # Theme, typography
│   │   ├── CoreCommon/          # Utilities
│   │   ├── CoreTesting/         # Test doubles
│   │   ├── FeatureHome/         # Home feature
│   │   ├── FeatureSettings/     # Settings feature
│   │   └── ...
│   └── Tests/
│       ├── CoreDataTests/
│       ├── FeatureHomeTests/
│       └── ...
└── MyAppTests/                  # App-level integration tests
```

## Xcode Workspace Setup

1. Create Xcode project (App template, SwiftUI lifecycle)
2. Create `AppModules/` directory at project root
3. Create `Package.swift` inside `AppModules/`
4. In Xcode: File → Add Package Dependencies → Add Local → select `AppModules/`
5. In App target: Build Phases → Link Binary with Libraries → add each module product

## Package.swift Configuration

```swift
// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "AppModules",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    products: [
        // Core modules
        .library(name: "CoreModel", targets: ["CoreModel"]),
        .library(name: "CoreData", targets: ["CoreData"]),
        .library(name: "CoreDatabase", targets: ["CoreDatabase"]),
        .library(name: "CoreNetwork", targets: ["CoreNetwork"]),
        .library(name: "CoreUI", targets: ["CoreUI"]),
        .library(name: "CoreDesignSystem", targets: ["CoreDesignSystem"]),
        .library(name: "CoreCommon", targets: ["CoreCommon"]),
        .library(name: "CoreTesting", targets: ["CoreTesting"]),

        // Feature modules
        .library(name: "FeatureHome", targets: ["FeatureHome"]),
        .library(name: "FeatureSettings", targets: ["FeatureSettings"]),
    ],
    dependencies: [
        // External dependencies (if any)
    ],
    targets: [
        // MARK: - Core

        .target(name: "CoreModel"),

        .target(
            name: "CoreCommon",
            dependencies: ["CoreModel"]
        ),

        .target(
            name: "CoreNetwork",
            dependencies: ["CoreModel"]
        ),

        .target(
            name: "CoreDatabase",
            dependencies: ["CoreModel"]
        ),

        .target(
            name: "CoreData",
            dependencies: [
                "CoreModel",
                "CoreDatabase",
                "CoreNetwork",
            ]
        ),

        .target(
            name: "CoreDesignSystem"
        ),

        .target(
            name: "CoreUI",
            dependencies: [
                "CoreModel",
                "CoreDesignSystem",
            ]
        ),

        .target(
            name: "CoreTesting",
            dependencies: ["CoreModel", "CoreData"]
        ),

        // MARK: - Features

        .target(
            name: "FeatureHome",
            dependencies: [
                "CoreData",
                "CoreUI",
                "CoreCommon",
            ]
        ),

        .target(
            name: "FeatureSettings",
            dependencies: [
                "CoreData",
                "CoreUI",
            ]
        ),

        // MARK: - Tests

        .testTarget(
            name: "CoreDataTests",
            dependencies: ["CoreData", "CoreTesting"]
        ),

        .testTarget(
            name: "CoreDatabaseTests",
            dependencies: ["CoreDatabase", "CoreTesting"]
        ),

        .testTarget(
            name: "FeatureHomeTests",
            dependencies: ["FeatureHome", "CoreTesting"]
        ),

        .testTarget(
            name: "FeatureSettingsTests",
            dependencies: ["FeatureSettings", "CoreTesting"]
        ),
    ]
)
```

---

## Build Settings

### Swift 6 Language Mode

In `Package.swift`, use `swift-tools-version: 6.0` (enables Swift 6 by default).

For Xcode project targets:
- Build Settings → Swift Compiler - Language → Swift Language Version → **Swift 6**

### Strict Concurrency Checking

Already enforced by Swift 6 language mode. For Swift 5.x targets migrating:

```swift
// Per-target in Package.swift
.target(
    name: "MyTarget",
    swiftSettings: [
        .enableExperimentalFeature("StrictConcurrency")
    ]
)
```

Or in Xcode: Build Settings → Strict Concurrency Checking → **Complete**

### Minimum Deployment Targets

| Requirement | Minimum iOS |
|-------------|-------------|
| @Observable | iOS 17 |
| SwiftData | iOS 17 |
| #Preview macro | iOS 17 |
| Swift Testing | iOS 16 (Xcode 16+) |
| NavigationStack | iOS 16 |
| AsyncStream | iOS 15 |

**Recommended minimum: iOS 17** for full feature set.

---

## Dependency Management

### Adding External Packages

In `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/pointfreeco/swift-dependencies", from: "1.0.0"),
],
targets: [
    .target(
        name: "CoreData",
        dependencies: [
            .product(name: "Dependencies", package: "swift-dependencies"),
        ]
    ),
]
```

### Version Pinning

`Package.resolved` is auto-generated and should be committed to source control for reproducible builds.

### Recommended External Dependencies

Keep external dependencies minimal. Prefer Apple frameworks:

| Need | Apple Framework | External Alternative |
|------|----------------|---------------------|
| Persistence | SwiftData | GRDB, Realm |
| Networking | URLSession | Alamofire |
| Image loading | AsyncImage | Kingfisher, Nuke |
| JSON | Codable | - |
| DI | Manual / @Environment | swift-dependencies |
| Testing | Swift Testing + XCTest | - |

---

## .gitignore

```gitignore
# Xcode
*.xcodeproj/xcuserdata/
*.xcworkspace/xcuserdata/
*.xcodeproj/project.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist
DerivedData/
*.moved-aside
*.ipa
*.dSYM.zip
*.dSYM

# Swift Package Manager
.build/
.swiftpm/

# macOS
.DS_Store

# IDE
*.swp
*.swo
*~
```
