---
name: android-app-builder
description: Create production-quality Android applications following Google's official architecture guidance and NowInAndroid best practices. Use when building Android apps with Kotlin, Jetpack Compose, MVVM architecture, Hilt dependency injection, Room database, or multi-module projects. Triggers on requests to create Android projects, screens, ViewModels, repositories, feature modules, or when asked about Android architecture patterns.
---

# Android Development

Build Android applications following Google's official architecture guidance, as demonstrated in the NowInAndroid reference app.

## Quick Reference

| Task | Reference File |
|------|----------------|
| Project structure & modules | [modularization.md](references/modularization.md) |
| Architecture layers (UI, Domain, Data) | [architecture.md](references/architecture.md) |
| Jetpack Compose patterns | [compose-patterns.md](references/compose-patterns.md) |
| Coroutines & Flow patterns | [coroutines.md](references/coroutines.md) |
| Gradle & build configuration | [gradle-setup.md](references/gradle-setup.md) |
| Testing approach | [testing.md](references/testing.md) |

## Workflow Decision Tree

**Creating a new project?**
→ Read [modularization.md](references/modularization.md) for project structure
→ Use templates in `assets/templates/`

**Adding a new feature?**
→ Create feature module with `api` and `impl` submodules
→ Follow patterns in [architecture.md](references/architecture.md)

**Building UI screens?**
→ Read [compose-patterns.md](references/compose-patterns.md)
→ Create Screen + ViewModel + UiState

**Setting up data layer?**
→ Read data layer section in [architecture.md](references/architecture.md)
→ Create Repository + DataSource + DAO

**Working with coroutines/Flow?**
→ Read [coroutines.md](references/coroutines.md)
→ Follow dispatcher and structured concurrency patterns

## Core Principles

1. **Offline-first**: Local database is source of truth, sync with remote
2. **Unidirectional data flow**: Events flow down, data flows up
3. **Reactive streams**: Use Kotlin Flow for all data exposure
4. **Modular by feature**: Each feature is self-contained with clear boundaries
5. **Testable by design**: Use interfaces and test doubles, no mocking libraries

## Architecture Layers

```
┌─────────────────────────────────────────┐
│              UI Layer                    │
│  (Compose Screens + ViewModels)          │
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
app/                    # App module - navigation, scaffolding
feature/
  ├── featurename/
  │   ├── api/          # Navigation keys (public)
  │   └── impl/         # Screen, ViewModel, DI (internal)
core/
  ├── data/             # Repositories
  ├── database/         # Room DAOs, entities
  ├── network/          # Retrofit, API models
  ├── model/            # Domain models (pure Kotlin)
  ├── common/           # Shared utilities
  ├── ui/               # Reusable Compose components
  ├── designsystem/     # Theme, icons, base components
  ├── datastore/        # Preferences storage
  └── testing/          # Test utilities
```

## Creating a New Feature

1. Create `feature:myfeature:api` module with navigation key
2. Create `feature:myfeature:impl` module with:
   - `MyFeatureScreen.kt` - Composable UI
   - `MyFeatureViewModel.kt` - State holder
   - `MyFeatureUiState.kt` - Sealed interface for states
   - `MyFeatureNavigation.kt` - Navigation setup
   - `MyFeatureModule.kt` - Hilt DI module

## Standard File Patterns

### ViewModel Pattern
```kotlin
@HiltViewModel
class MyFeatureViewModel @Inject constructor(
    private val myRepository: MyRepository,
) : ViewModel() {

    val uiState: StateFlow<MyFeatureUiState> = myRepository
        .getData()
        .map { data -> MyFeatureUiState.Success(data) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = MyFeatureUiState.Loading,
        )

    fun onAction(action: MyFeatureAction) {
        when (action) {
            is MyFeatureAction.ItemClicked -> handleItemClick(action.id)
            is MyFeatureAction.RefreshRequested -> refresh()
        }
    }

    private fun refresh() {
        viewModelScope.launch {
            myRepository.sync()
        }
    }
}
```

### UiState Pattern
```kotlin
sealed interface MyFeatureUiState {
    data object Loading : MyFeatureUiState
    data class Success(val items: List<Item>) : MyFeatureUiState
    data class Error(val message: String) : MyFeatureUiState
}
```

> **When to use individual StateFlows instead**: The sealed `UiState` pattern is idiomatic in Android because `collectAsStateWithLifecycle()` collects the entire object. However, for **independent UI elements** that update at different cadences (e.g., a snackbar message, a separate loading indicator for pull-to-refresh while content is visible, or a dialog), use separate `StateFlow` properties to avoid unnecessary recompositions of unrelated UI.

### Action Pattern
```kotlin
sealed interface MyFeatureAction {
    data class ItemClicked(val id: String) : MyFeatureAction
    data object RefreshRequested : MyFeatureAction
}
```

### Screen Pattern
```kotlin
@Composable
internal fun MyFeatureRoute(
    onNavigateToDetail: (String) -> Unit,
    viewModel: MyFeatureViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    MyFeatureScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onNavigateToDetail = onNavigateToDetail,
    )
}

@Composable
internal fun MyFeatureScreen(
    uiState: MyFeatureUiState,
    onAction: (MyFeatureAction) -> Unit,
    onNavigateToDetail: (String) -> Unit,
) {
    when (uiState) {
        is MyFeatureUiState.Loading -> LoadingIndicator()
        is MyFeatureUiState.Success -> ContentList(uiState.items, onAction)
        is MyFeatureUiState.Error -> ErrorMessage(uiState.message)
    }
}
```

### Repository Pattern
```kotlin
interface MyRepository {
    fun getData(): Flow<List<MyModel>>
    suspend fun updateItem(id: String, data: MyModel)
    suspend fun sync()
}

internal class OfflineFirstMyRepository @Inject constructor(
    private val localDataSource: MyDao,
    private val networkDataSource: MyNetworkApi,
) : MyRepository {

    override fun getData(): Flow<List<MyModel>> =
        localDataSource.getAll().map { entities ->
            entities.map { it.toModel() }
        }

    override suspend fun updateItem(id: String, data: MyModel) {
        localDataSource.upsert(data.toEntity())
    }

    override suspend fun sync() {
        val remoteItems = networkDataSource.getItems()
        localDataSource.upsertAll(remoteItems.map { it.toEntity() })
    }
}
```

### Navigation Pattern (Type-Safe)
```kotlin
// In api module
@Serializable
data class MyFeatureRoute(val id: String? = null)

fun NavController.navigateToMyFeature(id: String? = null) {
    navigate(MyFeatureRoute(id))
}

// In impl module
fun NavGraphBuilder.myFeatureScreen(
    onNavigateToDetail: (String) -> Unit,
) {
    composable<MyFeatureRoute> {
        MyFeatureRoute(onNavigateToDetail = onNavigateToDetail)
    }
}
```

### Hilt DI Module Pattern
```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {

    @Binds
    abstract fun bindMyRepository(
        impl: OfflineFirstMyRepository,
    ): MyRepository
}
```

## Target SDK & Language

| Setting | Value |
|---------|-------|
| compileSdk / targetSdk | 36 (Android 16 "Baklava") |
| minSdk | 26 (Android 8.0) |
| Kotlin | 2.3.10 |
| Compose BOM | 2026.02.01 |
| Java | 17 |
| AGP | 9.0.1 (Kotlin built-in, Gradle 9.1.0+ required) |
| Compose Compiler | Built into Kotlin 2.0+ (no separate version) |

## Key Dependencies

```kotlin
// Gradle version catalog (libs.versions.toml)
[versions]
kotlin = "2.3.10"
compose-bom = "2026.02.01"
hilt = "2.59.2"
room = "2.8.4"
coroutines = "1.10.1"

[libraries]
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "compose-bom" }
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
```

## Build Configuration

Use convention plugins in `build-logic/` for consistent configuration:
- `AndroidApplicationConventionPlugin` - App modules
- `AndroidLibraryConventionPlugin` - Library modules
- `AndroidFeatureConventionPlugin` - Feature modules
- `AndroidComposeConventionPlugin` - Compose setup (uses `kotlin-compose` plugin)
- `AndroidHiltConventionPlugin` - Hilt setup

**AGP 9.0 note**: Kotlin support is built into AGP 9.0 — remove `id("org.jetbrains.kotlin.android")` from plugin blocks.

See [gradle-setup.md](references/gradle-setup.md) for complete build configuration.
