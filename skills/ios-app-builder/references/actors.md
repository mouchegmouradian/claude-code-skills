# Swift Actors & Concurrency

Comprehensive guide to Swift actors, Sendable, structured concurrency, and their integration with SwiftUI and SwiftData.

## Table of Contents

1. [Actor Fundamentals](#actor-fundamentals)
2. [Actor Reentrancy](#actor-reentrancy)
3. [Global Actors](#global-actors)
4. [Actor Initialization](#actor-initialization)
5. [Sendable Protocol](#sendable-protocol)
6. [ModelActor for SwiftData](#modelactor-for-swiftdata)
7. [Actor + Repository Pattern](#actor--repository-pattern)
8. [Actor + SwiftUI Integration](#actor--swiftui-integration)
9. [Structured Concurrency](#structured-concurrency)
10. [Actor Anti-Patterns](#actor-anti-patterns)
11. [Decision Tree: Actor vs Struct vs Class](#decision-tree)
12. [Concurrency Profiling](#concurrency-profiling)

---

## Actor Fundamentals

Actors solve **data races** — when multiple threads access shared mutable state simultaneously. An actor serializes access to its mutable state, guaranteeing only one caller executes at a time.

### Declaration

```swift
actor ImageCache {
    private var cache: [URL: Data] = [:]

    func image(for url: URL) -> Data? {
        cache[url]
    }

    func store(_ data: Data, for url: URL) {
        cache[url] = data
    }

    func clear() {
        cache.removeAll()
    }
}
```

### Key Rules

- **All properties and methods are isolated by default.** Code inside the actor accesses state synchronously.
- **External callers must use `await`.** The caller suspends until the actor is available.
- **One caller at a time.** The actor's state is never accessed concurrently.
- **Actors are reference types.** They are classes under the hood, but with isolation.

### External Access

```swift
let cache = ImageCache()

// External: requires await (crosses isolation boundary)
let data = await cache.image(for: url)
await cache.store(imageData, for: url)

// Inside the actor itself: no await needed
actor ImageCache {
    func storeAndReturn(_ data: Data, for url: URL) -> Data? {
        store(data, for: url)     // No await — same isolation domain
        return image(for: url)    // No await — same isolation domain
    }
}
```

### `nonisolated` Methods

Methods that don't access mutable state can be marked `nonisolated` to avoid requiring `await`:

```swift
actor UserService {
    private var users: [String: User] = [:]
    let serviceName: String  // Immutable — safe to read without isolation

    nonisolated var description: String {
        "UserService: \(serviceName)"  // Only reads let property
    }

    nonisolated func makeURL(for userId: String) -> URL {
        URL(string: "https://api.example.com/users/\(userId)")!
    }
}

// No await needed for nonisolated members
let service = UserService()
let name = service.description       // Synchronous
let url = service.makeURL(for: "42") // Synchronous
```

---

## Actor Reentrancy

**Critical concept.** Actor state can change between suspension points (`await`). After any `await`, you must re-check assumptions about state.

### The Problem

```swift
// ❌ BUG: assumes cache unchanged after await
actor ImageLoader {
    private var cache: [URL: Data] = [:]

    func loadImage(from url: URL) async throws -> Data {
        if let cached = cache[url] {
            return cached
        }

        // ⚠️ SUSPENSION POINT — another caller can modify cache here
        let (data, _) = try await URLSession.shared.data(from: url)

        // BUG: may overwrite data from another concurrent caller
        // or may duplicate the network request
        cache[url] = data
        return data
    }
}
```

If two callers request the same URL simultaneously:
1. Caller A checks cache → miss, starts download
2. Caller B checks cache → miss (A hasn't finished), starts DUPLICATE download
3. Both store results, wasting bandwidth

### The Fix: Deduplicate In-Flight Requests

```swift
// ✅ CORRECT: deduplicates concurrent requests for same URL
actor ImageLoader {
    private var cache: [URL: Data] = [:]
    private var inProgress: [URL: Task<Data, Error>] = [:]

    func loadImage(from url: URL) async throws -> Data {
        // 1. Return cached result immediately
        if let cached = cache[url] {
            return cached
        }

        // 2. Join existing in-flight request if one exists
        if let existing = inProgress[url] {
            return try await existing.value
        }

        // 3. Start new request and store the Task for deduplication
        let task = Task {
            let (data, _) = try await URLSession.shared.data(from: url)
            return data
        }
        inProgress[url] = task

        do {
            let data = try await task.value
            // Re-check: another caller may have already cached
            cache[url] = data
            inProgress[url] = nil
            return data
        } catch {
            inProgress[url] = nil
            throw error
        }
    }
}
```

### Reentrancy Rule of Thumb

After **every** `await` inside an actor, ask: *"Could another caller have changed the state I'm relying on?"* If yes, re-validate before proceeding.

```swift
actor Counter {
    private var count = 0

    func incrementAfterDelay() async {
        let before = count
        await Task.yield()  // Suspension point
        // ❌ WRONG: count may have changed
        // count = before + 1

        // ✅ CORRECT: use current state
        count += 1
    }
}
```

---

## Global Actors

A global actor provides a **single shared isolation domain** that any type or function can join. The most common is `@MainActor`.

### @MainActor

Guarantees execution on the main thread. Use for **UI-related code only**.

```swift
// Entire class isolated to main actor
@MainActor
@Observable
final class SettingsViewModel {
    var theme: Theme = .system
    var notificationsEnabled = true

    func updateTheme(_ theme: Theme) {
        self.theme = theme  // Safe: always on main thread
    }
}
```

**@MainActor propagation**: When a class is marked `@MainActor`, all subclasses inherit that isolation. All properties and methods are main-actor-isolated unless explicitly marked `nonisolated`.

### When to Use @MainActor

| Use @MainActor | Use plain actor |
|----------------|-----------------|
| ViewModels | Data caches |
| UI-facing services | Network managers |
| Navigation coordinators | File I/O managers |
| Small, fast operations | Expensive computation |
| Anything updating UI state | Background data processing |

### Custom Global Actors

For app-wide isolation domains beyond the main thread:

```swift
@globalActor
actor DatabaseActor {
    static let shared = DatabaseActor()
}

// Any function or type can join this isolation domain
@DatabaseActor
func performMigration() async throws {
    // Guaranteed serialized with ALL other @DatabaseActor work
}

@DatabaseActor
class DatabaseService {
    var migrationVersion = 0

    func migrate() async throws {
        // Runs on DatabaseActor — serialized with performMigration()
    }
}
```

**Use custom global actors sparingly.** They create a single serial queue for all annotated code. Prefer plain actors for scoped isolation.

### Opting Out with `nonisolated`

```swift
@MainActor
final class ProfileViewModel {
    var name: String = ""

    // This doesn't need the main thread
    nonisolated func formatBio(_ text: String) -> String {
        text.trimmingCharacters(in: .whitespacesAndNewlines)
            .prefix(500)
            .description
    }
}
```

---

## Actor Initialization

In Swift 6, actor initializers run **outside** the actor's isolation domain. You cannot call isolated methods from `init`.

### The Problem

```swift
actor DataManager {
    private var cache: [String: Any] = [:]

    init() {
        // ❌ ERROR: Cannot call isolated method from nonisolated init
        // loadDefaults()
    }

    private func loadDefaults() {
        cache["version"] = "1.0"
    }
}
```

### Solution 1: Assign Directly in Init

```swift
actor DataManager {
    private var cache: [String: Any]

    init() {
        // ✅ Direct property assignment is allowed
        self.cache = ["version": "1.0"]
    }
}
```

### Solution 2: Factory Method

For complex initialization that requires isolated access:

```swift
actor DataManager {
    private var cache: [String: Any]

    private init(cache: [String: Any]) {
        self.cache = cache
    }

    static func create() async -> DataManager {
        let manager = DataManager(cache: [:])
        await manager.loadInitialData()
        return manager
    }

    private func loadInitialData() {
        // Runs inside actor isolation
        cache["version"] = "1.0"
        cache["initialized"] = true
    }
}

// Usage
let manager = await DataManager.create()
```

### Solution 3: Task in Caller

```swift
actor DataManager {
    private var cache: [String: Any] = [:]
    private(set) var isReady = false

    func initialize() async {
        // Load data, set up state
        cache["version"] = "1.0"
        isReady = true
    }
}

// Caller is responsible for initialization
let manager = DataManager()
await manager.initialize()
```

---

## Sendable Protocol

`Sendable` marks types that are safe to share across concurrency domains (actor boundaries, task boundaries).

### Automatic Sendable Conformance

**Value types** (structs, enums) are automatically Sendable when all stored properties are Sendable:

```swift
// ✅ Automatically Sendable — all properties are value types
struct UserProfile {
    let id: UUID
    var name: String
    var email: String
}

// ✅ Automatically Sendable — all associated values are Sendable
enum AppError: Error, Sendable {
    case networkFailure(String)
    case unauthorized
    case notFound(id: UUID)
}
```

### Class Sendable Conformance

Classes can conform to Sendable only if they are `final` with all `let` properties that are themselves Sendable:

```swift
// ✅ Sendable: final class, all let properties
final class APIConfiguration: Sendable {
    let baseURL: URL
    let apiKey: String
    let timeout: TimeInterval

    init(baseURL: URL, apiKey: String, timeout: TimeInterval = 30) {
        self.baseURL = baseURL
        self.apiKey = apiKey
        self.timeout = timeout
    }
}
```

### @unchecked Sendable

Escape hatch when you manage thread safety yourself. **Always document why it's safe.**

```swift
// Safety: All access is guarded by NSLock
final class ThreadSafeCache<Key: Hashable, Value>: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: [Key: Value] = [:]

    func get(_ key: Key) -> Value? {
        lock.withLock { storage[key] }
    }

    func set(_ key: Key, value: Value) {
        lock.withLock { storage[key] = value }
    }
}
```

**Rule:** Every `@unchecked Sendable` needs a comment explaining the safety invariant. Create a follow-up ticket to remove it when possible.

### @Sendable Closures

Closures crossing isolation boundaries must be `@Sendable` — they cannot capture mutable local variables:

```swift
// ❌ ERROR: @Sendable closure cannot capture mutable variable
var count = 0
Task { @Sendable in
    count += 1  // Compile error
}

// ✅ CORRECT: capture immutable value
let currentCount = count
Task { @Sendable in
    print(currentCount)
}

// ✅ CORRECT: use actor for shared mutable state
actor Counter {
    private var count = 0
    func increment() { count += 1 }
}
```

### Sendable Decision Tree

```
Is it a struct/enum with all Sendable properties?
  → Automatically Sendable ✅

Is it a final class with all let Sendable properties?
  → Conform to Sendable ✅

Is it an actor?
  → Automatically Sendable ✅ (actors are always Sendable)

Does it use internal locking (NSLock, Mutex, os_unfair_lock)?
  → Use @unchecked Sendable + document safety invariant

None of the above?
  → Redesign: extract mutable state into actor or use value types
```

---

## ModelActor for SwiftData

`@ModelActor` creates an actor with its own `ModelContext` for **background data operations**. This is the iOS equivalent of Android's Room DAO + background thread.

### When to Use

| Use @ModelActor | Use @MainActor ModelContext |
|-----------------|---------------------------|
| Background writes/inserts | Simple @Query reads in views |
| Batch operations | Small single-item saves |
| Data sync from network | User-initiated single edits |
| Complex queries/aggregations | Preview data |
| Import/export | |

### Basic @ModelActor

```swift
import SwiftData

@ModelActor
actor PersistenceActor {
    // The @ModelActor macro generates:
    //   let modelContainer: ModelContainer
    //   let modelExecutor: any ModelExecutor
    //   var modelContext: ModelContext { ... }

    func fetchTopics() throws -> [Topic] {
        let descriptor = FetchDescriptor<Topic>(
            sortBy: [SortDescriptor(\.name)]
        )
        return try modelContext.fetch(descriptor)
    }

    func fetchTopics(matching search: String) throws -> [Topic] {
        let predicate = #Predicate<Topic> { topic in
            topic.name.localizedStandardContains(search)
        }
        let descriptor = FetchDescriptor<Topic>(
            predicate: predicate,
            sortBy: [SortDescriptor(\.name)]
        )
        return try modelContext.fetch(descriptor)
    }

    func upsert(_ topic: Topic) throws {
        modelContext.insert(topic)
        try modelContext.save()
    }

    func upsertBatch(_ topics: [Topic]) throws {
        for topic in topics {
            modelContext.insert(topic)
        }
        try modelContext.save()
    }

    func delete(_ topic: Topic) throws {
        modelContext.delete(topic)
        try modelContext.save()
    }

    func deleteAll() throws {
        try modelContext.delete(model: Topic.self)
        try modelContext.save()
    }
}
```

### Creating a ModelActor

```swift
// From a ModelContainer (typically from @Environment)
let container = try ModelContainer(for: Topic.self)
let persistence = PersistenceActor(modelContainer: container)

// In SwiftUI, pass the container from environment
struct AppView: View {
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        ContentView()
            .task {
                let actor = PersistenceActor(
                    modelContainer: modelContext.container
                )
                try? await actor.upsertBatch(initialData)
            }
    }
}
```

### Important: Object Identity Across Contexts

SwiftData objects from a `@ModelActor` context cannot be directly used in another context (e.g., @MainActor). Pass persistent identifiers instead:

```swift
@ModelActor
actor PersistenceActor {
    // Return identifiers, not objects
    func fetchTopicIDs() throws -> [PersistentIdentifier] {
        let descriptor = FetchDescriptor<Topic>(
            sortBy: [SortDescriptor(\.name)]
        )
        return try modelContext.fetch(descriptor).map(\.persistentModelID)
    }
}

// On @MainActor, resolve identifiers in the main context
@MainActor
func resolveTopics(ids: [PersistentIdentifier], in context: ModelContext) -> [Topic] {
    ids.compactMap { context.model(for: $0) as? Topic }
}
```

---

## Actor + Repository Pattern

The offline-first repository pattern using actors. This is the iOS equivalent of Android's `OfflineFirstRepository` with Room + Retrofit.

```swift
// MARK: - Protocol

protocol TopicRepository: Sendable {
    func getTopics() async throws -> [Topic]
    func observeTopics() -> AsyncStream<[Topic]>
    func getTopic(id: String) async throws -> Topic?
    func saveTopic(_ topic: Topic) async throws
    func sync() async throws
}

// MARK: - Actor Implementation

actor OfflineFirstTopicRepository: TopicRepository {
    private let persistence: PersistenceActor
    private let network: TopicNetworkClient
    private var observerContinuations: [UUID: AsyncStream<[Topic]>.Continuation] = [:]

    init(persistence: PersistenceActor, network: TopicNetworkClient) {
        self.persistence = persistence
        self.network = network
    }

    func getTopics() async throws -> [Topic] {
        try await persistence.fetchTopics()
    }

    func observeTopics() -> AsyncStream<[Topic]> {
        AsyncStream { continuation in
            let id = UUID()
            // Send current data immediately
            Task {
                if let topics = try? await persistence.fetchTopics() {
                    continuation.yield(topics)
                }
            }
            // Store continuation for future updates
            Task { await self.addObserver(id: id, continuation: continuation) }
            continuation.onTermination = { _ in
                Task { await self.removeObserver(id: id) }
            }
        }
    }

    func getTopic(id: String) async throws -> Topic? {
        try await persistence.fetchTopics(matching: id).first
    }

    func saveTopic(_ topic: Topic) async throws {
        try await persistence.upsert(topic)
        await notifyObservers()
    }

    func sync() async throws {
        let remoteDTOs = try await network.fetchTopics()
        let topics = remoteDTOs.map { $0.toDomainModel() }
        try await persistence.upsertBatch(topics)
        await notifyObservers()
    }

    // MARK: - Private

    private func addObserver(id: UUID, continuation: AsyncStream<[Topic]>.Continuation) {
        observerContinuations[id] = continuation
    }

    private func removeObserver(id: UUID) {
        observerContinuations[id] = nil
    }

    private func notifyObservers() async {
        guard let topics = try? await persistence.fetchTopics() else { return }
        for (_, continuation) in observerContinuations {
            continuation.yield(topics)
        }
    }
}
```

### Network Client (Also Actor)

```swift
actor TopicNetworkClient: Sendable {
    private let session: URLSession
    private let baseURL: URL
    private let decoder = JSONDecoder()

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    func fetchTopics() async throws -> [TopicDTO] {
        let url = baseURL.appendingPathComponent("topics")
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }

        return try decoder.decode([TopicDTO].self, from: data)
    }
}

// DTO → Domain model mapping
struct TopicDTO: Codable {
    let id: String
    let name: String
    let description: String

    func toDomainModel() -> Topic {
        Topic(id: id, name: name, description: description)
    }
}

enum NetworkError: Error {
    case invalidResponse
    case decodingFailed
}
```

---

## Actor + SwiftUI Integration

### ViewModel Consuming Actor Repository

The ViewModel exposes individual properties (not a single state enum) so SwiftUI can track and re-render granularly. The Route owns it with `@State`, the Screen receives it as `let`.

```swift
@MainActor
@Observable
final class TopicListViewModel {
    // Individual properties — granular observation
    private(set) var topics: [Topic] = []
    private(set) var isLoading = false
    var errorMessage: String?

    private let repository: TopicRepository
    private var observeTask: Task<Void, Never>?

    init(repository: TopicRepository) {
        self.repository = repository
    }

    func onAppear() async {
        // Start observing (runs until view disappears)
        observeTask = Task {
            for await topics in repository.observeTopics() {
                self.topics = topics
            }
        }

        // Trigger initial sync
        await refresh()
    }

    func onDisappear() {
        observeTask?.cancel()
        observeTask = nil
    }

    func refresh() async {
        isLoading = true
        defer { isLoading = false }
        do {
            try await repository.sync()
        } catch {
            if topics.isEmpty {
                errorMessage = error.localizedDescription
            }
        }
    }

    func deleteTopic(id: String) async {
        do {
            try await repository.deleteTopic(id: id)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

### Route + Screen

```swift
// Route: owns ViewModel via @State
struct TopicListRoute: View {
    @State private var viewModel: TopicListViewModel
    let onNavigateToDetail: (String) -> Void

    init(repository: TopicRepository, onNavigateToDetail: @escaping (String) -> Void) {
        viewModel = TopicListViewModel(repository: repository)
        self.onNavigateToDetail = onNavigateToDetail
    }

    var body: some View {
        TopicListScreen(viewModel: viewModel, onNavigateToDetail: onNavigateToDetail)
            .task { await viewModel.onAppear() }
            .onDisappear { viewModel.onDisappear() }
            .refreshable { await viewModel.refresh() }
    }
}

// Screen: receives ViewModel as let, reads properties directly
struct TopicListScreen: View {
    let viewModel: TopicListViewModel
    let onNavigateToDetail: (String) -> Void

    var body: some View {
        List(viewModel.topics) { topic in
            Button {
                onNavigateToDetail(topic.id)
            } label: {
                VStack(alignment: .leading) {
                    Text(topic.name)
                        .font(.headline)
                    Text(topic.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .overlay {
            if viewModel.isLoading && viewModel.topics.isEmpty {
                ProgressView()
            }
        }
        .overlay {
            if let error = viewModel.errorMessage, viewModel.topics.isEmpty {
                ContentUnavailableView(
                    "Unable to Load",
                    systemImage: "wifi.slash",
                    description: Text(error)
                )
            }
        }
    }
}
```

---

## Structured Concurrency

### async let — Fixed Number of Parallel Operations

```swift
func loadProfile(userId: String) async throws -> UserProfile {
    async let user = fetchUser(userId)
    async let posts = fetchPosts(userId)
    async let followers = fetchFollowerCount(userId)

    // All three run concurrently; await collects results
    return try await UserProfile(
        user: user,
        posts: posts,
        followerCount: followers
    )
}
```

### TaskGroup — Dynamic Number of Parallel Operations

```swift
func loadThumbnails(for urls: [URL]) async throws -> [URL: Data] {
    try await withThrowingTaskGroup(of: (URL, Data).self) { group in
        for url in urls {
            group.addTask {
                let (data, _) = try await URLSession.shared.data(from: url)
                return (url, data)
            }
        }

        var results: [URL: Data] = [:]
        for try await (url, data) in group {
            results[url] = data
        }
        return results
    }
}
```

### Task — Unstructured (Use Sparingly)

```swift
// ✅ OK: bridging from synchronous to async context
func buttonTapped() {
    Task {
        await viewModel.refresh()
    }
}

// ⚠️ Task.detached — only with explicit justification
// Runs on a new executor, inherits no actor context
Task.detached(priority: .background) {
    // Use when you explicitly DON'T want actor isolation inheritance
    await heavyBackgroundWork()
}
```

### Prefer Structured Over Unstructured

| Pattern | Use When |
|---------|----------|
| `async let` | Fixed number of concurrent operations |
| `TaskGroup` | Dynamic/variable number of concurrent operations |
| `Task { }` | Bridging sync → async (e.g., button tap) |
| `Task.detached` | Must NOT inherit actor context (rare) |

**Never use `Task.detached` without a comment explaining why `Task { }` is insufficient.**

---

## Actor Anti-Patterns

### ❌ @MainActor as Blanket Solution

```swift
// ❌ DON'T: Putting everything on @MainActor causes UI jank
@MainActor
class DataProcessor {
    func processLargeDataset(_ data: [Record]) -> [ProcessedRecord] {
        // This blocks the main thread!
        data.map { expensiveTransform($0) }
    }
}

// ✅ DO: Use a plain actor for expensive work
actor DataProcessor {
    func processLargeDataset(_ data: [Record]) -> [ProcessedRecord] {
        data.map { expensiveTransform($0) }
    }
}
```

### ❌ Ignoring Reentrancy

```swift
// ❌ DON'T: Assume state unchanged after await
actor TokenManager {
    private var token: String?

    func getToken() async throws -> String {
        if let token { return token }
        let newToken = try await fetchToken()
        token = newToken  // May overwrite token set by concurrent caller
        return newToken
    }
}

// ✅ DO: Re-check after suspension
actor TokenManager {
    private var token: String?
    private var refreshTask: Task<String, Error>?

    func getToken() async throws -> String {
        if let token { return token }
        if let existing = refreshTask { return try await existing.value }

        let task = Task { try await fetchToken() }
        refreshTask = task
        let newToken = try await task.value
        token = newToken
        refreshTask = nil
        return newToken
    }
}
```

### ❌ Unnecessary Actors for Value Types

```swift
// ❌ DON'T: Value types are already thread-safe
actor PointStore {
    var point = CGPoint.zero
}

// ✅ DO: Just use the value type directly
struct GameState {
    var position = CGPoint.zero  // Struct is Sendable, no actor needed
}
```

### ❌ Actor Contention (Serial Bottleneck)

```swift
// ❌ DON'T: Single actor for ALL app data creates a bottleneck
actor AppDataStore {
    var users: [User] = []
    var posts: [Post] = []
    var settings: Settings = .default
    var analytics: [Event] = []
    // Every access serializes through one actor
}

// ✅ DO: Split into focused actors
actor UserStore { var users: [User] = [] }
actor PostStore { var posts: [Post] = [] }
actor AnalyticsStore { var events: [Event] = [] }
```

### ❌ Long Synchronous Work in Actors

```swift
// ❌ DON'T: Blocks other callers for the entire duration
actor ImageProcessor {
    func resize(_ images: [Data]) -> [Data] {
        images.map { heavyResizeOperation($0) }  // 30 seconds of blocking
    }
}

// ✅ DO: Break into chunks or use TaskGroup
actor ImageProcessor {
    func resize(_ images: [Data]) async -> [Data] {
        await withTaskGroup(of: Data.self) { group in
            for image in images {
                group.addTask { heavyResizeOperation(image) }
            }
            var results: [Data] = []
            for await result in group {
                results.append(result)
            }
            return results
        }
    }
}
```

### ❌ Accessing Actor State from nonisolated Context

```swift
// ❌ DON'T: Marking a method nonisolated then trying to access state
actor Cache {
    private var data: [String: Any] = [:]

    // This won't compile — can't access `data` from nonisolated
    nonisolated func unsafeRead(_ key: String) -> Any? {
        // data[key]  // ERROR: Actor-isolated property
        return nil
    }
}
```

---

## Decision Tree

```
Does it hold MUTABLE state shared across concurrency domains?
│
├─ YES → Use an Actor
│   │
│   ├─ Is it a singleton / app-wide service?
│   │   ├─ Does it need main-thread execution? → @MainActor class
│   │   └─ Does it NOT need main thread? → Consider @globalActor or global actor instance
│   │
│   ├─ Is it scoped to a feature / session?
│   │   └─ Use a plain actor
│   │
│   └─ Is it a SwiftData persistence layer?
│       └─ Use @ModelActor
│
├─ NO, but it needs reference semantics
│   │
│   ├─ Is it immutable (all let properties)?
│   │   └─ final class conforming to Sendable
│   │
│   └─ Does it have mutable state (var properties)?
│       ├─ Accessed from single isolation domain? → @MainActor class or plain class
│       └─ Accessed from multiple domains? → Convert to actor
│
└─ NO, and value semantics are fine
    └─ Use a Struct (automatically Sendable if all properties are)
```

---

## Concurrency Profiling

### Instruments: Swift Concurrency Template

1. Open Instruments → Swift Concurrency template
2. **Task Forest**: Shows task hierarchy, parent-child relationships
3. **Actor Queue**: Shows actor contention — high wait times indicate bottleneck
4. **Task Lifecycle**: Shows task creation, suspension, resumption

### Detecting Actor Contention

Signs of actor contention:
- UI stuttering when background work is happening
- Long wait times in Instruments actor queue
- Multiple tasks queued on same actor

**Fix**: Split actor into smaller, focused actors or move work to TaskGroup.

### @MainActor Violations

Enable strict concurrency checking to catch violations at compile time:

```
// In Package.swift
.target(
    name: "MyTarget",
    swiftSettings: [
        .enableExperimentalFeature("StrictConcurrency")
    ]
)

// Or in Xcode Build Settings
// Swift Compiler - Upcoming Features
// Strict Concurrency Checking: Complete
```

### Swift 6 Migration Strategy

1. **Start**: Set strict concurrency to "Targeted" (warnings only)
2. **Fix**: Address warnings one module at a time, starting from leaf modules (Model → Data → Features)
3. **Verify**: Ensure all tests pass with each module migration
4. **Complete**: Set to "Complete" (errors) when all warnings are resolved
5. **Enable**: Switch to Swift 6 language mode

### Common Migration Patterns

```swift
// GCD → async/await
// Before:
DispatchQueue.global().async {
    let result = process(data)
    DispatchQueue.main.async {
        self.updateUI(result)
    }
}

// After:
Task {
    let result = await process(data)
    await MainActor.run {
        updateUI(result)
    }
}

// Completion handlers → async/await
// Before:
func fetchUser(completion: @escaping (Result<User, Error>) -> Void) { ... }

// After:
func fetchUser() async throws -> User { ... }

// If you need to bridge legacy APIs:
func fetchUser() async throws -> User {
    try await withCheckedThrowingContinuation { continuation in
        fetchUser { result in
            continuation.resume(with: result)
        }
    }
}
```
