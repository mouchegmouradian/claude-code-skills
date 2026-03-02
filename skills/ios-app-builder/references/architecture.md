# Architecture

Three-layer architecture for iOS applications, adapted from Google's official Android architecture guidance for Swift, SwiftUI, and Swift Concurrency.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                       │
│  SwiftUI Views + @MainActor @Observable VMs      │
│  Owns: presentation logic, UI state, user input  │
├─────────────────────────────────────────────────┤
│                Domain Layer                      │
│  Use Cases (optional - for combining repos)      │
│  Owns: business logic, cross-repo operations     │
├─────────────────────────────────────────────────┤
│                 Data Layer                        │
│  Repository protocols + Actor implementations    │
│  Owns: data access, sync, caching, mapping       │
└─────────────────────────────────────────────────┘
```

**Data flows up** (repositories → use cases → ViewModels → views).
**Events flow down** (user actions → ViewModels → use cases → repositories).

---

## Data Layer

The data layer manages all data operations: local persistence, network requests, and synchronization.

### Principles

1. **Offline-first**: Local database (SwiftData) is the single source of truth
2. **Repository pattern**: Protocol defines contract, actor implements it
3. **Reactive streams**: Expose data as `AsyncStream<T>` for observation
4. **Model mapping**: Separate models for each boundary (DTO, entity, domain)

### Data Sources

| Source | Technology | Purpose |
|--------|-----------|---------|
| Local database | SwiftData + @ModelActor | Persistent storage, source of truth |
| Remote API | URLSession | Network data fetching |
| Preferences | UserDefaults / @AppStorage | Simple key-value settings |
| File storage | FileManager | Documents, caches, media |

### Repository Pattern

```swift
// Protocol: defines the contract
protocol TopicRepository: Sendable {
    func getTopics() async throws -> [Topic]
    func observeTopics() -> AsyncStream<[Topic]>
    func getTopic(id: String) async throws -> Topic?
    func saveTopic(_ topic: Topic) async throws
    func deleteTopic(id: String) async throws
    func sync() async throws
}
```

**Implementation is always an actor** for thread-safe shared state. See [actors.md](actors.md) for the full Actor + Repository Pattern.

### SwiftData @ModelActor

Background data operations run on a `@ModelActor` — a dedicated actor with its own `ModelContext`:

```swift
@ModelActor
actor TopicPersistence {
    func fetchAll() throws -> [TopicEntity] {
        let descriptor = FetchDescriptor<TopicEntity>(
            sortBy: [SortDescriptor(\.name)]
        )
        return try modelContext.fetch(descriptor)
    }

    func upsert(_ entity: TopicEntity) throws {
        modelContext.insert(entity)
        try modelContext.save()
    }

    func delete(id: String) throws {
        let predicate = #Predicate<TopicEntity> { $0.id == id }
        try modelContext.delete(model: TopicEntity.self, where: predicate)
        try modelContext.save()
    }
}
```

See [actors.md](actors.md) for comprehensive @ModelActor patterns.

### Model Mapping

Three model types at each boundary:

```
Network DTO          SwiftData Entity        Domain Model
(TopicDTO)     →     (TopicEntity)      →    (Topic)
Codable              @Model                   Plain struct
API shape            Storage shape             App shape
```

```swift
// Network DTO (Codable, matches API JSON)
struct TopicDTO: Codable, Sendable {
    let id: String
    let name: String
    let description: String
    let imageUrl: String?

    func toEntity() -> TopicEntity {
        TopicEntity(id: id, name: name, desc: description, imageUrl: imageUrl)
    }
}

// SwiftData Entity (persistent storage)
@Model
final class TopicEntity {
    @Attribute(.unique) var id: String
    var name: String
    var desc: String
    var imageUrl: String?

    init(id: String, name: String, desc: String, imageUrl: String?) {
        self.id = id
        self.name = name
        self.desc = desc
        self.imageUrl = imageUrl
    }

    func toDomainModel() -> Topic {
        Topic(id: id, name: name, description: desc, imageUrl: imageUrl.flatMap(URL.init))
    }
}

// Domain Model (pure Swift, used by UI and domain layers)
struct Topic: Identifiable, Equatable, Sendable {
    let id: String
    var name: String
    var description: String
    var imageUrl: URL?
}
```

### Network Layer

```swift
actor TopicNetworkClient {
    private let session: URLSession
    private let baseURL: URL
    private let decoder: JSONDecoder

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
    }

    func fetchTopics() async throws -> [TopicDTO] {
        let url = baseURL.appendingPathComponent("topics")
        let (data, response) = try await session.data(from: url)
        guard let http = response as? HTTPURLResponse,
              (200...299).contains(http.statusCode) else {
            throw NetworkError.invalidResponse
        }
        return try decoder.decode([TopicDTO].self, from: data)
    }
}
```

### Data Synchronization

```swift
// In the repository actor
func sync() async throws {
    // 1. Fetch from network
    let remoteDTOs = try await network.fetchTopics()

    // 2. Map DTOs to entities and persist
    let entities = remoteDTOs.map { $0.toEntity() }
    try await persistence.upsertBatch(entities)

    // 3. Notify observers (AsyncStream continuations)
    await notifyObservers()
}
```

For periodic background sync, use `BGAppRefreshTask`:

```swift
func scheduleSync() {
    let request = BGAppRefreshTaskRequest(identifier: "com.app.sync")
    request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
    try? BGTaskScheduler.shared.submit(request)
}
```

---

## Domain Layer

The domain layer is **optional**. Add it when you need to combine data from multiple repositories or encapsulate complex business logic.

### When to Create a Use Case

- Combining data from 2+ repositories
- Business logic that doesn't belong in a single repository
- Reusable logic shared across multiple ViewModels
- Complex data transformations

### Use Case Pattern

```swift
struct GetUserFeedUseCase: Sendable {
    private let topicRepository: TopicRepository
    private let userRepository: UserRepository

    init(topicRepository: TopicRepository, userRepository: UserRepository) {
        self.topicRepository = topicRepository
        self.userRepository = userRepository
    }

    func execute() async throws -> [FeedItem] {
        // Parallel fetch from multiple repositories
        async let topics = topicRepository.getTopics()
        async let preferences = userRepository.getPreferences()

        let (allTopics, userPrefs) = try await (topics, preferences)

        // Business logic: filter and sort based on user preferences
        return allTopics
            .filter { userPrefs.favoriteTopicIds.contains($0.id) }
            .sorted { $0.name < $1.name }
            .map { FeedItem(topic: $0, isFavorite: true) }
    }
}
```

### When NOT to Create a Use Case

- Single repository call → ViewModel calls repository directly
- Simple mapping → do it in the ViewModel
- One-off logic → inline in the ViewModel

---

## UI Layer

The UI layer consists of SwiftUI Views and `@MainActor @Observable` ViewModels.

### ViewModel Pattern

Expose individual properties — SwiftUI's `@Observable` tracks each accessed property per view, enabling granular re-renders. This also allows showing loading overlays while displaying stale content.

```swift
@MainActor
@Observable
final class TopicListViewModel {
    // State — individual properties for granular observation
    private(set) var topics: [Topic] = []
    private(set) var isLoading = false
    var errorMessage: String?

    // Dependencies
    private let repository: TopicRepository
    private var observeTask: Task<Void, Never>?

    init(repository: TopicRepository) {
        self.repository = repository
    }

    // MARK: - Lifecycle

    func onAppear() async {
        observeTask = Task {
            for await topics in repository.observeTopics() {
                self.topics = topics
            }
        }
        await sync()
    }

    func onDisappear() {
        observeTask?.cancel()
    }

    // MARK: - Actions

    func deleteTopic(id: String) async {
        do {
            try await repository.deleteTopic(id: id)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func refresh() async {
        await sync()
    }

    // MARK: - Private

    private func sync() async {
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
}
```

### View Composition (Route/Screen)

See [swiftui-patterns.md](swiftui-patterns.md) for detailed Route/Screen separation patterns.

- **Route** creates the ViewModel with `@State` (owns its lifecycle)
- **Screen** receives it as `let` — no wrapper needed, SwiftUI auto-tracks `@Observable`

```swift
// Route: owns ViewModel via @State, connects navigation
struct TopicListRoute: View {
    @State private var viewModel: TopicListViewModel

    init(repository: TopicRepository) {
        viewModel = TopicListViewModel(repository: repository)
    }

    var body: some View {
        TopicListScreen(viewModel: viewModel)
            .task { await viewModel.onAppear() }
            .onDisappear { viewModel.onDisappear() }
            .refreshable { await viewModel.refresh() }
    }
}

// Screen: receives ViewModel, reads properties directly
struct TopicListScreen: View {
    let viewModel: TopicListViewModel

    var body: some View {
        List(viewModel.topics) { topic in
            VStack(alignment: .leading) {
                Text(topic.name).font(.headline)
                Text(topic.description).font(.subheadline).foregroundStyle(.secondary)
            }
            .swipeActions {
                Button("Delete", role: .destructive) {
                    Task { await viewModel.deleteTopic(id: topic.id) }
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
                ContentUnavailableView("Error", systemImage: "exclamationmark.triangle", description: Text(error))
            }
        }
    }
}
```

---

## Full Data Flow Example

End-to-end flow for loading and displaying topics:

```
1. TopicListRoute.body renders → .task { await viewModel.onAppear() }

2. ViewModel.onAppear():
   a. Starts observeTask → repository.observeTopics() → AsyncStream
   b. Calls sync() → sets isLoading = true

3. Repository.sync():
   a. network.fetchTopics() → [TopicDTO]
   b. DTOs mapped to entities → persistence.upsertBatch()
   c. notifyObservers() → yields to AsyncStream continuations

4. AsyncStream emits [Topic] → observeTask receives
   a. ViewModel sets self.topics = topics (individual property)

5. SwiftUI detects @Observable property change
   a. Only views reading viewModel.topics re-render (granular observation)

6. User pulls to refresh → .refreshable { await viewModel.refresh() }
   → Back to step 3
```

---

## Dependency Injection

iOS does not have a Hilt equivalent. Use **manual initializer injection** with `@Environment` for distribution.

### Composition Root

```swift
@main
struct MyApp: App {
    // Create dependencies once at app level
    private let container: ModelContainer
    private let topicRepository: TopicRepository

    init() {
        let container = try! ModelContainer(for: TopicEntity.self)
        self.container = container

        let persistence = TopicPersistence(modelContainer: container)
        let network = TopicNetworkClient(baseURL: URL(string: "https://api.example.com")!)
        self.topicRepository = OfflineFirstTopicRepository(
            persistence: persistence,
            network: network
        )
    }

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                TopicListRoute(repository: topicRepository)
            }
        }
        .modelContainer(container)
    }
}
```

### Environment-Based Distribution

For deeply nested views, use `@Environment`:

```swift
// Define environment key
private struct TopicRepositoryKey: EnvironmentKey {
    static let defaultValue: TopicRepository = PreviewTopicRepository()
}

extension EnvironmentValues {
    var topicRepository: TopicRepository {
        get { self[TopicRepositoryKey.self] }
        set { self[TopicRepositoryKey.self] = newValue }
    }
}

// Inject at root
ContentView()
    .environment(\.topicRepository, liveRepository)

// Consume in any descendant
struct SomeDeepView: View {
    @Environment(\.topicRepository) private var repository
}
```
