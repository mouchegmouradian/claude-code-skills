# Testing

Testing strategy using Swift Testing framework and protocol-based test doubles. No mocking libraries.

---

## Testing Philosophy

1. **No mocking libraries** (no OCMock, no Cuckoo, no Mockolo). Use hand-written test doubles that implement real protocols.
2. **Test behavior, not implementation**. Assert on outputs and state, not on method call counts.
3. **Test doubles exercise more production code** than mocks — they implement the actual protocol contract.
4. **Swift Testing** (`@Test`) for unit tests. XCTest for UI tests.

---

## Test Doubles

### Test Repository

```swift
import CoreData
import CoreModel

final class TestTopicRepository: TopicRepository, @unchecked Sendable {
    // Safety: Only accessed from test (single-threaded)
    private var topics: [Topic] = []
    private var continuations: [AsyncStream<[Topic]>.Continuation] = []
    private var syncError: Error?

    // MARK: - Test Hooks

    func setTopics(_ topics: [Topic]) {
        self.topics = topics
        for continuation in continuations {
            continuation.yield(topics)
        }
    }

    func setSyncError(_ error: Error?) {
        self.syncError = error
    }

    // MARK: - TopicRepository

    func getTopics() async throws -> [Topic] {
        topics
    }

    func observeTopics() -> AsyncStream<[Topic]> {
        AsyncStream { continuation in
            continuation.yield(topics)
            continuations.append(continuation)
        }
    }

    func getTopic(id: String) async throws -> Topic? {
        topics.first { $0.id == id }
    }

    func saveTopic(_ topic: Topic) async throws {
        if let index = topics.firstIndex(where: { $0.id == topic.id }) {
            topics[index] = topic
        } else {
            topics.append(topic)
        }
        for continuation in continuations {
            continuation.yield(topics)
        }
    }

    func deleteTopic(id: String) async throws {
        topics.removeAll { $0.id == id }
        for continuation in continuations {
            continuation.yield(topics)
        }
    }

    func sync() async throws {
        if let error = syncError {
            throw error
        }
    }
}
```

### Test Network Client

```swift
final class TestNetworkClient: @unchecked Sendable {
    // Safety: Only accessed from test (single-threaded)
    private var responses: [String: Any] = [:]
    private var error: Error?

    func setResponse<T: Sendable>(_ response: T, for endpoint: String) {
        responses[endpoint] = response
    }

    func setError(_ error: Error) {
        self.error = error
    }

    func fetch<T>(endpoint: String) async throws -> T {
        if let error { throw error }
        guard let response = responses[endpoint] as? T else {
            fatalError("No response set for endpoint: \(endpoint)")
        }
        return response
    }
}
```

### Sample Data

```swift
// In CoreTesting module
import CoreModel

public enum TestData {
    public static let topics: [Topic] = [
        Topic(id: "1", name: "Swift Concurrency", description: "Actors, async/await"),
        Topic(id: "2", name: "SwiftUI", description: "Declarative UI framework"),
        Topic(id: "3", name: "SwiftData", description: "Persistence framework"),
    ]

    public static let singleTopic = topics[0]

    public static let emptyTopics: [Topic] = []
}
```

---

## Testing ViewModels

### Swift Testing Framework

```swift
import Testing
@testable import FeatureHome

@Suite("HomeViewModel")
struct HomeViewModelTests {

    @Test("starts with empty state")
    func startsEmpty() async {
        let repository = TestTopicRepository()
        let viewModel = await HomeViewModel(repository: repository)

        await #expect(viewModel.topics.isEmpty)
        await #expect(viewModel.isLoading == false)
        await #expect(viewModel.errorMessage == nil)
    }

    @Test("loads topics on appear")
    func loadsTopicsOnAppear() async {
        let repository = TestTopicRepository()
        repository.setTopics(TestData.topics)

        let viewModel = await HomeViewModel(repository: repository)
        await viewModel.onAppear()

        // Wait for observation to deliver
        try? await Task.sleep(for: .milliseconds(100))

        await #expect(viewModel.topics == TestData.topics)
        await #expect(viewModel.isLoading == false)
    }

    @Test("shows error when sync fails with no cached data")
    func showsErrorOnSyncFailure() async {
        let repository = TestTopicRepository()
        repository.setSyncError(NetworkError.invalidResponse)

        let viewModel = await HomeViewModel(repository: repository)
        await viewModel.onAppear()

        try? await Task.sleep(for: .milliseconds(100))

        await #expect(viewModel.errorMessage != nil)
        await #expect(viewModel.topics.isEmpty)
    }

    @Test("delete removes topic")
    func deleteRemovesTopic() async {
        let repository = TestTopicRepository()
        repository.setTopics(TestData.topics)

        let viewModel = await HomeViewModel(repository: repository)
        await viewModel.onAppear()
        try? await Task.sleep(for: .milliseconds(100))

        await viewModel.deleteTopic(id: "1")
        try? await Task.sleep(for: .milliseconds(100))

        await #expect(!viewModel.topics.contains { $0.id == "1" })
    }
}
```

### Parameterized Tests

```swift
@Test("filters topics by search text", arguments: [
    ("Swift", 2),   // "Swift Concurrency" and "SwiftUI" and "SwiftData"
    ("UI", 1),      // "SwiftUI"
    ("xyz", 0),     // No match
    ("", 3),        // Empty search returns all
])
func filtersTopics(search: String, expectedCount: Int) async {
    let repository = TestTopicRepository()
    repository.setTopics(TestData.topics)

    let viewModel = await SearchViewModel(repository: repository)
    await viewModel.onAppear()
    viewModel.searchText = search

    #expect(viewModel.filteredTopics.count == expectedCount)
}
```

---

## Testing Actors

```swift
import Testing
@testable import CoreData

@Suite("ImageCache Actor")
struct ImageCacheTests {

    @Test("stores and retrieves data")
    func storeAndRetrieve() async {
        let cache = ImageCache()
        let testData = Data("image-bytes".utf8)
        let url = URL(string: "https://example.com/img.png")!

        await cache.store(testData, for: url)
        let retrieved = await cache.image(for: url)

        #expect(retrieved == testData)
    }

    @Test("returns nil for missing key")
    func missingKey() async {
        let cache = ImageCache()
        let url = URL(string: "https://example.com/missing.png")!

        let result = await cache.image(for: url)

        #expect(result == nil)
    }

    @Test("clear removes all entries")
    func clearCache() async {
        let cache = ImageCache()
        let url = URL(string: "https://example.com/img.png")!
        await cache.store(Data("test".utf8), for: url)

        await cache.clear()

        let result = await cache.image(for: url)
        #expect(result == nil)
    }
}
```

### Testing Actor Reentrancy

```swift
@Test("handles concurrent loads for same URL")
func concurrentLoads() async throws {
    let loader = ImageLoader()
    let url = URL(string: "https://example.com/photo.jpg")!

    // Launch multiple concurrent loads
    async let result1 = loader.loadImage(from: url)
    async let result2 = loader.loadImage(from: url)
    async let result3 = loader.loadImage(from: url)

    let (data1, data2, data3) = try await (result1, result2, result3)

    // All should return the same data (deduplicated)
    #expect(data1 == data2)
    #expect(data2 == data3)
}
```

---

## Testing Async Code

### Basic Async Tests

Swift Testing natively supports async:

```swift
@Test("fetches user profile")
func fetchProfile() async throws {
    let client = TestNetworkClient()
    client.setResponse(UserDTO(id: "1", name: "Alice"), for: "users/1")

    let user: UserDTO = try await client.fetch(endpoint: "users/1")

    #expect(user.name == "Alice")
}
```

### Testing AsyncStream

```swift
@Test("repository emits updates")
func observeEmitsUpdates() async {
    let repository = TestTopicRepository()
    repository.setTopics([TestData.singleTopic])

    var received: [[Topic]] = []
    let stream = repository.observeTopics()

    for await topics in stream {
        received.append(topics)
        if received.count >= 2 { break }

        // Trigger an update
        repository.setTopics(TestData.topics)
    }

    #expect(received.count == 2)
    #expect(received[0].count == 1)
    #expect(received[1].count == 3)
}
```

### Confirmation API

For testing that an event occurs:

```swift
@Test("calls completion after save")
func saveCallsCompletion() async {
    await confirmation { confirmed in
        let saver = DataSaver(onComplete: { confirmed() })
        await saver.save(TestData.singleTopic)
    }
}
```

---

## Swift Testing Quick Reference

### Attributes

| Attribute | Purpose |
|-----------|---------|
| `@Test` | Marks a test function |
| `@Test("description")` | Test with display name |
| `@Test(.tags(.networking))` | Tagged test |
| `@Test(arguments: [...])` | Parameterized test |
| `@Suite` | Groups related tests |
| `@Suite(.serialized)` | Tests run sequentially |

### Assertions

| Macro | Purpose |
|-------|---------|
| `#expect(condition)` | Assert condition is true |
| `#expect(a == b)` | Assert equality |
| `#expect(throws: MyError.self) { try foo() }` | Assert specific error thrown |
| `#require(condition)` | Assert + stop test if fails |
| `#require(try expression)` | Unwrap or fail |
| `Issue.record("message")` | Record a test failure |

### Tags

```swift
extension Tag {
    @Tag static var networking: Self
    @Tag static var persistence: Self
    @Tag static var ui: Self
}

@Test(.tags(.networking))
func fetchData() async throws { /* ... */ }

// Run tagged tests: swift test --filter .tags:networking
```

---

## UI Testing with XCTest

For testing SwiftUI views in a running app:

```swift
import XCTest

final class TopicListUITests: XCTestCase {
    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launchArguments = ["--uitesting"]
        app.launch()
    }

    func testTopicListDisplaysItems() {
        let list = app.collectionViews.firstMatch
        XCTAssertTrue(list.waitForExistence(timeout: 5))

        let firstCell = list.cells.firstMatch
        XCTAssertTrue(firstCell.exists)
    }

    func testPullToRefresh() {
        let list = app.collectionViews.firstMatch
        list.swipeDown()

        // Verify refresh indicator appeared
        let refreshControl = app.activityIndicators.firstMatch
        XCTAssertTrue(refreshControl.waitForExistence(timeout: 2))
    }

    func testNavigateToDetail() {
        let firstCell = app.collectionViews.cells.firstMatch
        XCTAssertTrue(firstCell.waitForExistence(timeout: 5))
        firstCell.tap()

        // Verify detail screen appeared
        let backButton = app.navigationBars.buttons.firstMatch
        XCTAssertTrue(backButton.waitForExistence(timeout: 2))
    }
}
```

### Accessibility Identifiers

Set identifiers in SwiftUI for reliable UI test targeting:

```swift
struct TopicListScreen: View {
    var body: some View {
        List(topics) { topic in
            TopicRow(topic: topic)
                .accessibilityIdentifier("topic-row-\(topic.id)")
        }
        .accessibilityIdentifier("topic-list")
    }
}

// In UI test
let specificRow = app.cells["topic-row-42"]
XCTAssertTrue(specificRow.waitForExistence(timeout: 5))
```

---

## Test Organization

```
Tests/
├── CoreDataTests/
│   ├── TopicRepositoryTests.swift     # Repository logic
│   └── UserRepositoryTests.swift
├── CoreDatabaseTests/
│   └── PersistenceActorTests.swift    # @ModelActor tests
├── CoreNetworkTests/
│   └── NetworkClientTests.swift       # Network layer tests
├── FeatureHomeTests/
│   ├── HomeViewModelTests.swift       # ViewModel state + actions
│   └── HomeScreenSnapshotTests.swift  # Visual regression (optional)
└── FeatureSettingsTests/
    └── SettingsViewModelTests.swift
```

### Test Naming Convention

```swift
@Test("verb + condition + expected result")
func deleteTopic_whenTopicExists_removesFromList() async { /* ... */ }
```

Or use Swift Testing's descriptive string:

```swift
@Test("removes topic from list when it exists")
func deleteExistingTopic() async { /* ... */ }
```
