# Kotlin Coroutines & Flow

Comprehensive guide to coroutines, Flow, and structured concurrency for Android development.

## Table of Contents
1. [Dispatcher Usage](#dispatcher-usage)
2. [viewModelScope Patterns](#viewmodelscope-patterns)
3. [Structured Concurrency](#structured-concurrency)
4. [Error Handling](#error-handling)
5. [Flow Operators](#flow-operators)
6. [StateFlow & SharedFlow](#stateflow--sharedflow)
7. [Testing Coroutines](#testing-coroutines)
8. [Common Anti-Patterns](#common-anti-patterns)

## Dispatcher Usage

### Dispatcher Types

| Dispatcher | Use For | Thread Pool |
|-----------|---------|-------------|
| `Dispatchers.Main` | UI updates, small logic | Main thread only |
| `Dispatchers.IO` | Network, disk, database | Shared pool (64+ threads) |
| `Dispatchers.Default` | CPU-intensive computation | Shared pool (CPU core count) |
| `Dispatchers.Unconfined` | Testing only | Runs on caller's thread |

### Dispatcher Rules

- **Never perform IO on `Main`** — blocks the UI thread
- **Never update UI from `IO` or `Default`** — crashes
- **Room and Retrofit handle dispatching internally** — no need to wrap calls in `withContext(Dispatchers.IO)` if using suspend functions
- **Use `withContext` for CPU-heavy transformations** in repositories

### withContext Pattern

```kotlin
class OfflineFirstMyRepository @Inject constructor(
    private val localDataSource: MyDao,
    private val networkDataSource: MyNetworkApi,
    @Dispatcher(NiaDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) : MyRepository {

    override suspend fun sync() {
        val remoteItems = networkDataSource.getItems()
        // Heavy mapping — move off the calling thread
        val entities = withContext(ioDispatcher) {
            remoteItems.map { it.toEntity() }
        }
        localDataSource.upsertAll(entities)
    }
}
```

### Custom Dispatchers with Hilt

```kotlin
// In core:common
@Qualifier
@Retention(AnnotationRetention.RUNTIME)
annotation class Dispatcher(val niaDispatcher: NiaDispatchers)

enum class NiaDispatchers {
    Default,
    IO,
}

// DI Module
@Module
@InstallIn(SingletonComponent::class)
object DispatchersModule {
    @Provides
    @Dispatcher(NiaDispatchers.IO)
    fun providesIODispatcher(): CoroutineDispatcher = Dispatchers.IO

    @Provides
    @Dispatcher(NiaDispatchers.Default)
    fun providesDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default
}
```

## viewModelScope Patterns

### Collecting to StateFlow

```kotlin
@HiltViewModel
class MyViewModel @Inject constructor(
    myRepository: MyRepository,
) : ViewModel() {

    val uiState: StateFlow<MyUiState> = myRepository
        .getData()
        .map { MyUiState.Success(it) }
        .catch { emit(MyUiState.Error(it.message ?: "Unknown error")) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = MyUiState.Loading,
        )
}
```

**Why `WhileSubscribed(5_000)`?** Keeps the upstream flow active for 5 seconds after the last subscriber (the UI) disappears. This survives configuration changes (screen rotation) without restarting the flow, but stops collecting when the user navigates away.

### Combining Multiple Flows

```kotlin
val uiState: StateFlow<HomeUiState> = combine(
    topicsRepository.getTopics(),
    userDataRepository.userData,
) { topics, userData ->
    HomeUiState.Success(
        topics = topics.mapToFollowableTopics(userData),
    )
}
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = HomeUiState.Loading,
    )
```

### Fire-and-Forget Actions

```kotlin
fun onAction(action: MyAction) {
    when (action) {
        is MyAction.BookmarkClicked -> {
            viewModelScope.launch {
                userDataRepository.setBookmarked(action.id, action.bookmarked)
            }
        }
    }
}
```

## Structured Concurrency

### coroutineScope — Parallel Decomposition

All child coroutines must succeed. If any child fails, all siblings are cancelled.

```kotlin
suspend fun syncAll() = coroutineScope {
    launch { topicsRepository.sync() }
    launch { newsRepository.sync() }
    // Both run concurrently. If either fails, the other is cancelled.
}
```

### supervisorScope — Independent Children

Children can fail independently without cancelling siblings.

```kotlin
suspend fun syncAllBestEffort() = supervisorScope {
    launch {
        try { topicsRepository.sync() }
        catch (e: Exception) { /* log, continue */ }
    }
    launch {
        try { newsRepository.sync() }
        catch (e: Exception) { /* log, continue */ }
    }
}
```

### async/await — Return Values from Parallel Work

```kotlin
suspend fun loadDashboard(): Dashboard = coroutineScope {
    val user = async { userRepository.getUser() }
    val stats = async { statsRepository.getStats() }
    val notifications = async { notifRepository.getRecent() }

    Dashboard(
        user = user.await(),
        stats = stats.await(),
        notifications = notifications.await(),
    )
}
```

## Error Handling

### In ViewModels

```kotlin
fun refresh() {
    viewModelScope.launch {
        try {
            repository.sync()
        } catch (e: CancellationException) {
            throw e  // NEVER swallow CancellationException
        } catch (e: Exception) {
            _errorMessage.value = e.message
        }
    }
}
```

### In Flows with catch

```kotlin
val uiState = repository.getData()
    .map<List<Item>, UiState> { UiState.Success(it) }
    .catch { emit(UiState.Error(it.message ?: "Unknown error")) }
    .stateIn(...)
```

### Critical Rule: Never Catch CancellationException

```kotlin
// WRONG — breaks structured concurrency
try {
    someWork()
} catch (e: Exception) {
    // This catches CancellationException, preventing coroutine cancellation
    log(e)
}

// CORRECT — rethrow CancellationException
try {
    someWork()
} catch (e: CancellationException) {
    throw e
} catch (e: Exception) {
    log(e)
}

// ALSO CORRECT — use runCatching carefully
val result = runCatching { someWork() }
    .onFailure { if (it is CancellationException) throw it }
```

## Flow Operators

### Essential Operators

| Operator | Use Case |
|----------|----------|
| `map` | Transform each emission |
| `combine` | Merge multiple flows (re-emits when any input changes) |
| `flatMapLatest` | Switch to new flow, cancel previous |
| `distinctUntilChanged` | Skip duplicate emissions |
| `catch` | Handle upstream errors |
| `onStart` | Emit initial value or perform setup |
| `debounce` | Wait for pause in emissions (search input) |
| `conflate` | Skip intermediate values when collector is slow |

### Search with flatMapLatest + debounce

```kotlin
private val searchQuery = MutableStateFlow("")

val searchResults: StateFlow<List<Item>> = searchQuery
    .debounce(300)
    .distinctUntilChanged()
    .flatMapLatest { query ->
        if (query.isBlank()) flowOf(emptyList())
        else repository.search(query)
    }
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = emptyList(),
    )

fun onSearchQueryChanged(query: String) {
    searchQuery.value = query
}
```

### Combining Flows for Complex UI State

```kotlin
val uiState: StateFlow<ForYouUiState> = combine(
    getUserNewsResourcesUseCase(),
    userDataRepository.userData,
    refreshState,
) { newsResources, userData, isRefreshing ->
    ForYouUiState.Success(
        feed = newsResources,
        isRefreshing = isRefreshing,
        shouldShowOnboarding = !userData.shouldHideOnboarding,
    )
}
    .stateIn(...)
```

## StateFlow & SharedFlow

### StateFlow

- Always has a current value (`.value`)
- Replays the latest value to new subscribers
- Uses `distinctUntilChanged` internally (skips duplicate emissions)
- Use for: UI state, current values

### SharedFlow

- No initial value required
- Configurable replay cache
- Does NOT skip duplicates
- Use for: one-shot events, actions that should fire even with same value

```kotlin
// Events that should not be replayed on configuration change
private val _events = MutableSharedFlow<UiEvent>()
val events: SharedFlow<UiEvent> = _events.asSharedFlow()

// Use Channel for strictly one-time events (e.g., navigation)
private val _navigationEvents = Channel<NavigationEvent>()
val navigationEvents = _navigationEvents.receiveAsFlow()
```

## Testing Coroutines

### TestDispatcher Setup

```kotlin
class TestDispatcherRule(
    private val testDispatcher: TestDispatcher = UnconfinedTestDispatcher(),
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

### runTest

```kotlin
@Test
fun `repository emits data from database`() = runTest {
    val dao = TestTopicDao()
    dao.upsertTopics(testEntities)

    val repository = OfflineFirstTopicsRepository(dao, testNetwork)
    val topics = repository.getTopics().first()

    assertEquals(testEntities.size, topics.size)
}
```

### Turbine for Flow Testing

```kotlin
@Test
fun `uiState transitions from Loading to Success`() = runTest {
    viewModel.uiState.test {
        assertEquals(MyUiState.Loading, awaitItem())

        testRepository.sendData(testItems)

        val success = awaitItem()
        assertIs<MyUiState.Success>(success)
        assertEquals(testItems.size, success.items.size)

        cancelAndIgnoreRemainingEvents()
    }
}
```

### Testing with StandardTestDispatcher

Use `StandardTestDispatcher` when you need explicit control over coroutine execution order (vs `UnconfinedTestDispatcher` which runs eagerly):

```kotlin
@Test
fun `loading state is emitted before data`() = runTest {
    val testDispatcher = StandardTestDispatcher(testScheduler)
    Dispatchers.setMain(testDispatcher)

    val viewModel = MyViewModel(testRepository)

    assertEquals(MyUiState.Loading, viewModel.uiState.value)

    testRepository.sendData(testItems)
    advanceUntilIdle()

    assertIs<MyUiState.Success>(viewModel.uiState.value)

    Dispatchers.resetMain()
}
```

## Common Anti-Patterns

### GlobalScope

```kotlin
// WRONG — leaks coroutines, no structured cancellation
GlobalScope.launch {
    repository.sync()
}

// CORRECT — use viewModelScope or a scoped CoroutineScope
viewModelScope.launch {
    repository.sync()
}
```

### Blocking the Main Thread

```kotlin
// WRONG — blocks UI thread
fun getData(): List<Item> = runBlocking {
    repository.getItems()
}

// CORRECT — make the function suspend
suspend fun getData(): List<Item> =
    repository.getItems()
```

### Unnecessary withContext for Room/Retrofit

```kotlin
// UNNECESSARY — Room suspend functions already switch to IO
suspend fun getItems() = withContext(Dispatchers.IO) {
    dao.getAllItems()
}

// CORRECT — just call it directly
suspend fun getItems() = dao.getAllItems()
```

### Collecting Flow in init

```kotlin
// WRONG — starts collection before UI is ready, wastes resources
@HiltViewModel
class MyViewModel @Inject constructor(repo: MyRepository) : ViewModel() {
    var items: List<Item> = emptyList()

    init {
        viewModelScope.launch {
            repo.getData().collect { items = it }
        }
    }
}

// CORRECT — use stateIn for lazy collection
@HiltViewModel
class MyViewModel @Inject constructor(repo: MyRepository) : ViewModel() {
    val items: StateFlow<List<Item>> = repo.getData()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList(),
        )
}
```

### Launching in Composables

```kotlin
// WRONG — launches new coroutine on every recomposition
@Composable
fun MyScreen(viewModel: MyViewModel) {
    viewModel.loadData()  // If this launches a coroutine, BAD
}

// CORRECT — use LaunchedEffect for side effects
@Composable
fun MyScreen(viewModel: MyViewModel) {
    LaunchedEffect(Unit) {
        viewModel.loadData()
    }
}
```
