# Claude iOS Skill

A comprehensive Claude Code skill for building production-quality iOS applications following Apple's official architecture guidance, modern Swift concurrency patterns (actors, async/await), and SwiftUI best practices.

## Overview

This skill teaches Claude to generate iOS code that follows:

- **Apple's official architecture guidance** (WWDC 2023-2025)
- **Modern Swift Concurrency** with actors, async/await, and Sendable
- **SwiftUI best practices** including Route/Screen separation and State-as-Bridge
- **Offline-first data layer** with SwiftData and @ModelActor
- **Multi-module architecture** via Swift Package Manager
- **Test-driven development** with Swift Testing and protocol-based test doubles

## Installation

Clone this repository into your Claude Code skills directory:

```bash
git clone <repo-url> ~/.claude/skills/claude-ios-skill
```

Or add as a skill reference in your Claude Code configuration.

## Quick Reference

| Topic | File |
|-------|------|
| Architecture (UI/Domain/Data layers) | [references/architecture.md](references/architecture.md) |
| SwiftUI patterns & navigation | [references/swiftui-patterns.md](references/swiftui-patterns.md) |
| Swift Actors & concurrency | [references/actors.md](references/actors.md) |
| Project & build configuration | [references/project-setup.md](references/project-setup.md) |
| Multi-module structure | [references/modularization.md](references/modularization.md) |
| Testing strategy | [references/testing.md](references/testing.md) |

## Core Principles

1. **Offline-first** — SwiftData is source of truth, sync with remote
2. **Unidirectional data flow** — Events down, data up
3. **Reactive streams** — AsyncSequence/AsyncStream for all data exposure
4. **Modular by feature** — Self-contained SPM modules
5. **Testable by design** — Protocols and test doubles, no mocking libraries
6. **Actor-isolated concurrency** — Actors for shared state, @MainActor for UI

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Swift 6 (strict concurrency) |
| UI | SwiftUI |
| Architecture | MVVM + @Observable |
| Concurrency | Swift Actors, async/await |
| Persistence | SwiftData + @ModelActor |
| Networking | URLSession |
| Modules | Swift Package Manager |
| Testing | Swift Testing + XCTest |
| Min Target | iOS 17+ |

## Project Structure

```
App/                        # App target (@main, navigation)
AppModules/                 # Local SPM package
├── Sources/
│   ├── CoreModel/          # Domain models (pure Swift)
│   ├── CoreData/           # Repository protocols + actor impls
│   ├── CoreDatabase/       # SwiftData @Model + @ModelActor
│   ├── CoreNetwork/        # URLSession, DTOs
│   ├── CoreUI/             # Reusable SwiftUI components
│   ├── CoreDesignSystem/   # Theme, colors, typography
│   ├── CoreCommon/         # Utilities, extensions
│   ├── CoreTesting/        # Test doubles, sample data
│   └── Feature*/           # Feature modules (Route+Screen+VM)
└── Tests/
    └── Feature*Tests/      # Feature tests
```

## Feature Generation

Generate a new feature module:

```bash
python scripts/generate_feature.py user-profile --path /path/to/AppModules
```

This creates Route, Screen, ViewModel, and test files.

## Acknowledgments

- [Apple Developer Documentation](https://developer.apple.com/documentation/) — Official architecture guidance
- [Axiom](https://charleswiltgen.github.io/Axiom/) — iOS development skills for Claude Code
- [Swift Concurrency Agent Skill](https://github.com/AvdLee/Swift-Concurrency-Agent-Skill) — Concurrency patterns

## License

MIT License. See [LICENSE](LICENSE).
