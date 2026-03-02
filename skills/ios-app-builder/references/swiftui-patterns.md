# SwiftUI Patterns

Best practices for SwiftUI development, incorporating Apple's official guidance (WWDC 2023-2025) and Axiom-inspired patterns.

## Table of Contents

1. [Route-Screen Separation](#route-screen-separation)
2. [State-as-Bridge Pattern](#state-as-bridge-pattern)
3. [Property Wrapper Decision Tree](#property-wrapper-decision-tree)
4. [@Observable Model Pattern](#observable-model-pattern)
5. [Navigation Patterns](#navigation-patterns)
6. [Component Patterns](#component-patterns)
7. [Preview Patterns](#preview-patterns)
8. [Anti-Patterns](#anti-patterns)

---

## Route-Screen Separation

Split every feature view into two views:

- **Route**: Owns the ViewModel (`@State`), handles navigation callbacks, lifecycle (`.task`, `.refreshable`)
- **Screen**: Receives the ViewModel (`let`), renders UI, calls ViewModel methods directly

### Why

- Screen is previewable (create a ViewModel with sample data)
- Route handles the "wiring" (ViewModel creation, navigation, DI)
- Clear boundary between lifecycle concerns and UI layout
- SwiftUI auto-tracks `@Observable` on `let` properties — no wrapper needed

### Property Wrapper Decision (WWDC 2023)

| View role | Wrapper | Example |
|-----------|---------|---------|
| Creates the instance | `@State` | `@State private var viewModel = MyVM()` |
| Receives from parent | `let` (none) | `let viewModel: MyVM` |
| Needs `$` bindings | `@Bindable` | `@Bindable var viewModel = viewModel` |
| Shared app-wide | `@Environment` | `@Environment(AppState.self) var appState` |

### Pattern

```swift
// Route: owns ViewModel via @State, connects to app
struct SettingsRoute: View {
    @State private var viewModel: SettingsViewModel
    let onNavigateToProfile: () -> Void

    init(repository: SettingsRepository, onNavigateToProfile: @escaping () -> Void) {
        viewModel = SettingsViewModel(repository: repository)
        self.onNavigateToProfile = onNavigateToProfile
    }

    var body: some View {
        SettingsScreen(viewModel: viewModel, onNavigateToProfile: onNavigateToProfile)
            .task { await viewModel.onAppear() }
            .navigationTitle("Settings")
    }
}

// Screen: receives ViewModel as let, reads properties directly
struct SettingsScreen: View {
    let viewModel: SettingsViewModel
    let onNavigateToProfile: () -> Void

    var body: some View {
        Form {
            Section("Account") {
                Button("Profile") { onNavigateToProfile() }
            }
            Section("Preferences") {
                // Use @Bindable locally for two-way bindings
                @Bindable var viewModel = viewModel
                Toggle("Notifications", isOn: $viewModel.notificationsEnabled)
                Picker("Theme", selection: $viewModel.selectedTheme) {
                    ForEach(Theme.allCases, id: \.self) { theme in
                        Text(theme.displayName).tag(theme)
                    }
                }
            }
        }
        .overlay {
            if viewModel.isLoading {
                ProgressView()
            }
        }
    }
}
```

### ViewModel for Above Example

```swift
@MainActor
@Observable
final class SettingsViewModel {
    private(set) var isLoading = false
    var notificationsEnabled = false
    var selectedTheme: Theme = .system
    var errorMessage: String?

    private let repository: SettingsRepository

    init(repository: SettingsRepository) {
        self.repository = repository
    }

    func onAppear() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let settings = try await repository.getSettings()
            notificationsEnabled = settings.notificationsEnabled
            selectedTheme = settings.theme
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

---

## State-as-Bridge Pattern

From WWDC 2025: Keep UI state changes **synchronous** for animations. Use state as a bridge between async work and the UI.

### Problem

Async functions create suspension points that break animations:

```swift
// ❌ Animation timing is uncertain
struct LoadingView: View {
    @State private var isLoading = false

    var body: some View {
        Button("Load") {
            Task {
                isLoading = true                    // Synchronous ✅
                await performExpensiveWork()         // ⚠️ Suspension
                isLoading = false                   // ❌ Might miss animation frame
            }
        }
        .scaleEffect(isLoading ? 1.2 : 1.0)
        .animation(.spring, value: isLoading)
    }
}
```

### Solution

Separate synchronous state changes (for animations) from async work:

```swift
// ✅ Synchronous state changes for animations, async work separate
struct LoadingView: View {
    @State private var isLoading = false

    var body: some View {
        Button("Load") {
            // Synchronous: animation works correctly
            withAnimation {
                isLoading = true
            }

            // Async: runs independently
            Task {
                await performExpensiveWork()

                // Synchronous: animation works correctly
                withAnimation {
                    isLoading = false
                }
            }
        }
        .scaleEffect(isLoading ? 1.2 : 1.0)
    }
}
```

### In ViewModels

Move async work to the ViewModel, keep View synchronous:

```swift
@MainActor
@Observable
final class SearchViewModel {
    var searchText = ""
    var results: [SearchResult] = []
    var isSearching = false

    func search() async {
        isSearching = true  // Synchronous on @MainActor → animation safe
        do {
            results = try await repository.search(query: searchText)
        } catch {
            results = []
        }
        isSearching = false // Synchronous on @MainActor → animation safe
    }
}
```

---

## Property Wrapper Decision Tree

```
Which property wrapper should I use?
│
├─ Does the VIEW OWN this state (created and managed by this view)?
│  └─ @State
│     Examples: form inputs, local toggles, sheet presentation, view-owned ViewModel
│     Lifetime: tied to the view
│
├─ Does the PARENT own it and you need two-way binding?
│  └─ @Binding
│     Examples: child toggle, child text field, sheet dismissal
│     Lifetime: parent's lifetime
│
├─ Is it an @Observable model you need bindings ($) for?
│  └─ @Bindable
│     Examples: editing a model passed from parent
│     Purpose: enables $ syntax on @Observable properties
│
├─ Is it provided via the environment (app-wide, scene-wide)?
│  └─ @Environment
│     Examples: modelContext, colorScheme, custom dependencies
│     Lifetime: scope where .environment() was called
│
├─ Is it a SwiftData query?
│  └─ @Query
│     Examples: fetching all items, filtered/sorted fetch
│     Lifetime: tied to ModelContext in environment
│
└─ None of the above (just reading, no mutation or binding needed)?
   └─ Plain property (let or var)
      Examples: data passed from parent for display only
      No wrapper needed
```

### Code Examples

```swift
// @State — View owns this
struct CreateTopicView: View {
    @State private var name = ""
    @State private var description = ""
    @State private var showingPreview = false

    var body: some View {
        Form {
            TextField("Name", text: $name)
            TextField("Description", text: $description)
            Button("Preview") { showingPreview = true }
        }
        .sheet(isPresented: $showingPreview) {
            TopicPreview(name: name, description: description)
        }
    }
}

// @Binding — Parent owns, child mutates
struct ToggleRow: View {
    let title: String
    @Binding var isOn: Bool

    var body: some View {
        Toggle(title, isOn: $isOn)
    }
}

// @Bindable — Need $ on @Observable
struct TopicEditor: View {
    @Bindable var topic: Topic  // Topic is @Observable

    var body: some View {
        TextField("Name", text: $topic.name)
    }
}

// @Environment — App-wide dependency
struct TopicListView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.topicRepository) private var repository

    var body: some View { /* ... */ }
}

// @Query — SwiftData fetch
struct AllTopicsView: View {
    @Query(sort: \TopicEntity.name) private var topics: [TopicEntity]

    var body: some View {
        List(topics) { topic in
            Text(topic.name)
        }
    }
}

// Plain property — just reading
struct TopicRow: View {
    let topic: Topic  // No wrapper needed

    var body: some View {
        VStack(alignment: .leading) {
            Text(topic.name).font(.headline)
            Text(topic.description).font(.subheadline)
        }
    }
}
```

---

## @Observable Model Pattern

`@Observable` (iOS 17+) replaces `ObservableObject`. SwiftUI automatically tracks which properties are accessed during `body` and only re-renders when those specific properties change.

### Basic Pattern

```swift
@Observable
class ShoppingCart {
    var items: [CartItem] = []
    var couponCode: String?

    var totalPrice: Double {
        items.reduce(0) { $0 + $1.price * Double($1.quantity) }
    }

    var itemCount: Int {
        items.reduce(0) { $0 + $1.quantity }
    }

    func addItem(_ item: CartItem) {
        items.append(item)
    }

    func removeLast() {
        items.removeLast()
    }
}
```

### How Tracking Works

```swift
struct CartView: View {
    let cart: ShoppingCart  // No wrapper needed!

    var body: some View {
        VStack {
            // SwiftUI tracks: cart.itemCount, cart.totalPrice
            Text("Items: \(cart.itemCount)")
            Text("Total: $\(cart.totalPrice, specifier: "%.2f")")

            // cart.couponCode is NOT tracked here
            // → changes to couponCode won't re-render this view
        }
    }
}
```

Only properties **accessed in body** trigger re-renders. This is more granular than the old `ObservableObject` pattern.

### @Observable vs ObservableObject

| @Observable (iOS 17+) | ObservableObject (legacy) |
|----------------------|--------------------------|
| Automatic property tracking | Must mark each property with @Published |
| No wrapper needed in views | Requires @ObservedObject or @StateObject |
| Granular updates | Entire object triggers update |
| Works with `let` in views | Requires @ObservedObject var |

**Always use `@Observable` for new code.** Only use `ObservableObject` when supporting iOS 16 and below.

---

## Navigation Patterns

### NavigationStack with Type-Safe Routes

```swift
// Define routes as a Hashable enum
enum AppRoute: Hashable {
    case topicDetail(id: String)
    case settings
    case profile(userId: String)
}

struct RootView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            TopicListRoute(
                repository: topicRepository,
                onNavigateToDetail: { id in
                    path.append(AppRoute.topicDetail(id: id))
                }
            )
            .navigationDestination(for: AppRoute.self) { route in
                switch route {
                case .topicDetail(let id):
                    TopicDetailRoute(id: id, repository: topicRepository)
                case .settings:
                    SettingsRoute(repository: settingsRepository, onNavigateToProfile: {
                        path.append(AppRoute.profile(userId: "me"))
                    })
                case .profile(let userId):
                    ProfileRoute(userId: userId)
                }
            }
        }
    }
}
```

### Coordinator Pattern (Complex Navigation)

For apps with complex navigation, deep linking, or multiple entry points:

```swift
@Observable
class AppCoordinator {
    var path: [AppRoute] = []

    func showTopicDetail(id: String) {
        path.append(.topicDetail(id: id))
    }

    func showSettings() {
        path.append(.settings)
    }

    func popToRoot() {
        path.removeAll()
    }

    func handleDeepLink(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return }
        if components.path.hasPrefix("/topics/"),
           let id = components.path.split(separator: "/").last {
            path = [.topicDetail(id: String(id))]
        }
    }
}

struct CoordinatedRootView: View {
    @State private var coordinator = AppCoordinator()

    var body: some View {
        NavigationStack(path: $coordinator.path) {
            HomeScreen(coordinator: coordinator)
                .navigationDestination(for: AppRoute.self) { route in
                    // ... route handling
                }
        }
        .onOpenURL { url in
            coordinator.handleDeepLink(url)
        }
    }
}
```

### Tab-Based Navigation

```swift
struct MainTabView: View {
    @State private var selectedTab = Tab.home

    enum Tab {
        case home, search, profile
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            NavigationStack {
                HomeRoute(repository: homeRepository)
            }
            .tabItem { Label("Home", systemImage: "house") }
            .tag(Tab.home)

            NavigationStack {
                SearchRoute(repository: searchRepository)
            }
            .tabItem { Label("Search", systemImage: "magnifyingglass") }
            .tag(Tab.search)

            NavigationStack {
                ProfileRoute(userId: "me")
            }
            .tabItem { Label("Profile", systemImage: "person") }
            .tag(Tab.profile)
        }
    }
}
```

---

## Component Patterns

### Stateless Components

Components should receive data and callbacks — no internal state management:

```swift
struct TopicCard: View {
    let topic: Topic
    let onTap: () -> Void
    let onBookmark: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 8) {
                Text(topic.name)
                    .font(.headline)
                Text(topic.description)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .swipeActions(edge: .trailing) {
            Button(action: onBookmark) {
                Label("Bookmark", systemImage: "bookmark")
            }
            .tint(.blue)
        }
    }
}
```

### Lists with Proper Identity

```swift
struct TopicList: View {
    let topics: [Topic]
    let onAction: (TopicListAction) -> Void

    var body: some View {
        List {
            ForEach(topics) { topic in  // Topic: Identifiable
                TopicCard(
                    topic: topic,
                    onTap: { onAction(.topicTapped(id: topic.id)) },
                    onBookmark: { onAction(.bookmarkTopic(id: topic.id)) }
                )
            }
            .onDelete { indexSet in
                for index in indexSet {
                    onAction(.deleteTopic(id: topics[index].id))
                }
            }
        }
    }
}
```

### Reusable Modifiers

```swift
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(.regularMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .shadow(radius: 2)
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
}

// Usage
Text("Hello").cardStyle()
```

---

## Preview Patterns

### Basic #Preview

Create a ViewModel, set its properties, and pass it to the Screen:

```swift
#Preview {
    let viewModel = TopicListViewModel(repository: PreviewTopicRepository())
    // Set properties directly for preview state
    viewModel.topics = Topic.sampleData
    return TopicListScreen(viewModel: viewModel)
}
```

### Multiple State Previews

```swift
#Preview("With Data") {
    let viewModel = TopicListViewModel(repository: PreviewTopicRepository())
    viewModel.topics = Topic.sampleData
    return TopicListScreen(viewModel: viewModel)
}

#Preview("Loading") {
    let viewModel = TopicListViewModel(repository: PreviewTopicRepository())
    viewModel.isLoading = true
    return TopicListScreen(viewModel: viewModel)
}

#Preview("Error") {
    let viewModel = TopicListViewModel(repository: PreviewTopicRepository())
    viewModel.errorMessage = "Network connection lost"
    return TopicListScreen(viewModel: viewModel)
}

#Preview("Empty") {
    let viewModel = TopicListViewModel(repository: PreviewTopicRepository())
    return TopicListScreen(viewModel: viewModel)
}
```

### Sample Data Factory

```swift
extension Topic {
    static let sampleData: [Topic] = [
        Topic(id: "1", name: "Swift Concurrency", description: "Learn about actors, async/await, and structured concurrency"),
        Topic(id: "2", name: "SwiftUI", description: "Build declarative user interfaces"),
        Topic(id: "3", name: "SwiftData", description: "Persist and query data with Swift"),
    ]

    static let sample = sampleData[0]
}
```

---

## Anti-Patterns

### ❌ Logic in View Body

```swift
// ❌ DON'T: computation and formatting in body
struct OrderView: View {
    let orders: [Order]

    var body: some View {
        let formatter = NumberFormatter()  // Created every render!
        formatter.numberStyle = .currency

        let filtered = orders.filter { $0.total > 100 }  // Computed every render!

        return List(filtered) { order in
            Text(formatter.string(from: order.total as NSNumber)!)
        }
    }
}

// ✅ DO: extract to ViewModel
@MainActor @Observable
final class OrderViewModel {
    let orders: [Order]
    private let formatter = NumberFormatter()

    var filteredOrders: [Order] {
        orders.filter { $0.total > 100 }
    }

    init(orders: [Order]) {
        self.orders = orders
        formatter.numberStyle = .currency
    }

    func formattedTotal(_ order: Order) -> String {
        formatter.string(from: order.total as NSNumber) ?? "$0.00"
    }
}
```

### ❌ Wrong Property Wrapper

```swift
// ❌ @State for passed-in model (creates a copy, loses parent changes)
struct DetailView: View {
    @State var item: Item  // ❌
}

// ✅ Plain property or @Bindable
struct DetailView: View {
    let item: Item           // Read-only
    // or
    @Bindable var item: Item // If need $item bindings
}
```

### ❌ God ViewModel

```swift
// ❌ One ViewModel for everything
@Observable class AppViewModel {
    var users: [User] = []
    var posts: [Post] = []
    var settings: Settings = .default
    // ... 50 more properties
}

// ✅ Split by feature
@Observable class UserListViewModel { /* ... */ }
@Observable class PostFeedViewModel { /* ... */ }
@Observable class SettingsViewModel { /* ... */ }
```

### ❌ Async Without Boundaries

```swift
// ❌ await inside withAnimation
withAnimation {
    await loadData()  // Suspension breaks animation!
}

// ✅ Synchronous state change, async work separate
withAnimation { isLoading = true }
Task {
    await loadData()
    withAnimation { isLoading = false }
}
```
