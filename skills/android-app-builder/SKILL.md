---
name: android-app-builder
description: Create Android applications scaled to project complexity. Automatically detects whether to use a simple single-module architecture (no DI, DataStore), a standard Hilt + Room single-module structure, or full NowInAndroid multi-module production architecture. Use when building Android apps with Kotlin, Jetpack Compose, and MVVM. Triggers on requests to create Android projects, screens, ViewModels, repositories, feature modules, or when asked about Android architecture patterns.
---

# Android Development

Build Android applications following Google's official architecture guidance, as demonstrated in the NowInAndroid reference app.

## Quick Reference

| Task | Reference File |
|------|----------------|
| **Complexity tier selection** | [complexity-tiers.md](references/complexity-tiers.md) |
| Project structure & modules | [modularization.md](references/modularization.md) |
| Architecture layers (UI, Domain, Data) | [architecture.md](references/architecture.md) |
| Jetpack Compose patterns | [compose-patterns.md](references/compose-patterns.md) |
| Coroutines & Flow patterns | [coroutines.md](references/coroutines.md) |
| Gradle & build configuration | [gradle-setup.md](references/gradle-setup.md) |
| Testing approach | [testing.md](references/testing.md) |

## Step 0: Detect Complexity Tier

**Before writing any code**, classify the project into one of three tiers. This determines every architectural decision that follows.

### Detection Heuristics

Apply these signals in order. The first confident match wins.

**Tier 1 — Simple** (default for ambiguous small projects):
- Described as: demo, prototype, personal app, learning project, side project, sample, or proof-of-concept
- 1–3 distinct user-facing features
- Features are independent — no described need to share data across screens
- No described need for background processing or scheduled work
- No mention of teams, multi-developer workflow, or production deployment
- Examples: tip calculator, flashcard app, habit tracker, weather viewer, unit converter

**Tier 2 — Standard**:
- 3–6 distinct user-facing features
- Some features share a repository or data model (e.g., "profile data shown on both home and settings")
- Described as a "real app" or "production" but built by a small team (1–3 developers)
- Needs Hilt for testability or future scaling, but no current need for module isolation
- Examples: personal finance tracker, recipe app with favorites/search/detail, fitness app with history and goals

**Tier 3 — Production** (current default behavior, unchanged):
- 6+ distinct user-facing features, or
- Multiple teams working in parallel, or
- Described as needing module isolation, independent delivery, or feature flags per team, or
- Complex background sync (WorkManager with multiple syncable repositories), or
- Existing large codebase being extended

### Fallback: Ask When Uncertain

If the description is ambiguous, ask **exactly one** clarifying question before proceeding:

> "To choose the right architecture, how many distinct features does this app need, and is this a personal/prototype app or something for a team or production release?"

Use the answer to re-apply the heuristics above.

### After Classification

State the selected tier and its rationale in one sentence before generating any code. Example:

> "This is a Tier 1 (Simple) project — a personal prototype with 2 features and no shared data layer."

Then follow **only** the blueprint for that tier. Do not mix patterns across tiers.

---

## Workflow Decision Tree

**After detecting the tier (see Step 0 above):**

**Tier 1 — Creating a new project?**
→ Single `app/` module only — no feature or core submodules
→ No Hilt — use companion object ViewModel factory (see [Simple Tier Patterns](#simple-tier-patterns-tier-1-only) below)
→ No Room — use DataStore or in-memory state
→ See [complexity-tiers.md](references/complexity-tiers.md) for the full Tier 1 blueprint

**Tier 2 — Creating a new project?**
→ Single module with feature packages: `ui/featurename/`, `data/`, `di/`
→ Hilt for DI (KSP setup required)
→ Room if persistence is needed
→ No `build-logic/`, no module split
→ See [complexity-tiers.md](references/complexity-tiers.md) for the full Tier 2 blueprint

**Tier 3 — Creating a new project?**
→ Read [modularization.md](references/modularization.md) for project structure
→ Use templates in `assets/templates/`

**Adding a new feature? (all tiers)**
→ Tier 1/2: Add a new package under `app/src/main/.../ui/featurename/`
→ Tier 3: Create `feature:myfeature:api` + `feature:myfeature:impl` modules

**Building UI screens? (all tiers)**
→ Read [compose-patterns.md](references/compose-patterns.md)
→ Always create Route + Screen composables (Route/Screen split applies at every tier)
→ Always use sealed UiState (Loading/Success/Error)

**Setting up data layer?**
→ Tier 1: In-memory or DataStore; concrete class, no interface required for simple cases
→ Tier 2/3: Interface + implementation; read data layer section in [architecture.md](references/architecture.md)

**Working with coroutines/Flow? (all tiers)**
→ Read [coroutines.md](references/coroutines.md)
→ Follow dispatcher and structured concurrency patterns

## Core Principles

1. **MVVM + UDF** *(all tiers)*: ViewModels expose `StateFlow`, screens react to state changes; events flow down, data flows up
2. **Sealed UiState** *(all tiers)*: Always model Loading/Success/Error states with a sealed interface
3. **Route/Screen split** *(all tiers)*: Route composable handles ViewModel wiring; Screen composable receives plain data only
4. **No mocking libraries** *(all tiers)*: Use test doubles that implement the same interfaces
5. **Reactive streams** *(all tiers)*: Use Kotlin Flow for all data exposure
6. **Offline-first** *(Tier 3 default, optional Tier 2)*: Local database is source of truth when network sync is required
7. **Modular by feature** *(Tier 3 only)*: Each feature is a separate Gradle module with clear api/impl boundaries
8. **Testable by design** *(all tiers)*: DI enables this via Hilt (Tier 2/3) or constructor injection via factory (Tier 1)

## Simple Tier Patterns (Tier 1 Only)

Use these patterns **only** when the project is classified as Tier 1. Do not add Hilt or multi-module structure to Tier 1 projects.

### Project Structure (Tier 1)

```
app/
└── src/main/kotlin/com/example/app/
    ├── MainActivity.kt
    ├── AppNavigation.kt           # NavHost + all routes in one file
    ├── data/
    │   └── MyRepository.kt        # Concrete class, no interface required
    └── ui/
        └── featurename/
            ├── FeatureNameRoute.kt
            ├── FeatureNameScreen.kt
            ├── FeatureNameViewModel.kt
            └── FeatureNameUiState.kt
```

### ViewModel Factory Pattern (Tier 1 — No Hilt)

```kotlin
class FeatureNameViewModel(
    private val repository: MyRepository,
) : ViewModel() {

    val uiState: StateFlow<FeatureNameUiState> = repository
        .getData()
        .map { data -> FeatureNameUiState.Success(data) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = FeatureNameUiState.Loading,
        )

    fun onAction(action: FeatureNameAction) {
        when (action) {
            is FeatureNameAction.ItemClicked -> handleItemClick(action.id)
        }
    }

    companion object {
        fun factory(repository: MyRepository): ViewModelProvider.Factory =
            viewModelFactory {
                initializer { FeatureNameViewModel(repository) }
            }
    }
}
```

### Route Pattern (Tier 1 — No `hiltViewModel()`)

```kotlin
@Composable
internal fun FeatureNameRoute(
    onNavigateToDetail: (String) -> Unit,
    repository: MyRepository,
    viewModel: FeatureNameViewModel = viewModel(
        factory = FeatureNameViewModel.factory(repository)
    ),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    FeatureNameScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onNavigateToDetail = onNavigateToDetail,
    )
}
```

### Repository Pattern (Tier 1 — Concrete Class, DataStore)

```kotlin
class MyRepository(
    private val dataStore: DataStore<Preferences>,
) {
    val items: Flow<List<MyItem>> = dataStore.data
        .map { prefs -> prefs[MY_ITEMS_KEY]?.let { deserialize(it) } ?: emptyList() }

    suspend fun addItem(item: MyItem) {
        dataStore.edit { prefs ->
            val current = prefs[MY_ITEMS_KEY]?.let { deserialize(it) } ?: emptyList()
            prefs[MY_ITEMS_KEY] = serialize(current + item)
        }
    }

    companion object {
        val MY_ITEMS_KEY = stringPreferencesKey("my_items")
    }
}
```

### MainActivity Wiring (Tier 1 — No Application Subclass Needed)

```kotlin
class MainActivity : ComponentActivity() {

    private val repository by lazy {
        MyRepository(applicationContext.dataStore)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppTheme {
                AppNavigation(repository = repository)
            }
        }
    }
}

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "app_data")
```

### Navigation (Tier 1 — String Routes, All in One File)

```kotlin
@Composable
fun AppNavigation(repository: MyRepository) {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = "feature_name") {
        composable("feature_name") {
            FeatureNameRoute(
                onNavigateToDetail = { id -> navController.navigate("detail/$id") },
                repository = repository,
            )
        }
        composable("detail/{id}") { backStackEntry ->
            val id = backStackEntry.arguments?.getString("id") ?: return@composable
            DetailRoute(id = id, repository = repository)
        }
    }
}
```

> Tier 1 uses string routes for simplicity. Tier 2/3 use type-safe `@Serializable` routes.

### `build.gradle.kts` (Tier 1 — No KSP, No Hilt)

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.example.app"
    compileSdk = 36
    defaultConfig { minSdk = 26; targetSdk = 36 }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures { compose = true }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.datastore.preferences)
    debugImplementation(libs.androidx.compose.ui.tooling)
}
```

No `build-logic/`, no `ksp`, no Hilt compiler. This is intentional.

---

## Standard Tier Patterns (Tier 2 Only)

Use these patterns when the project is classified as Tier 2. Single module with Hilt; no `build-logic/` convention plugins or multi-module structure.

### Project Structure (Tier 2)

```
app/
└── src/main/kotlin/com/example/app/
    ├── MainActivity.kt              # @AndroidEntryPoint
    ├── AppNavigation.kt
    ├── di/
    │   └── AppModule.kt             # @Module @InstallIn(SingletonComponent)
    ├── model/
    │   └── MyModel.kt
    ├── data/
    │   ├── MyRepository.kt          # Interface
    │   └── MyRepositoryImpl.kt      # @Inject constructor
    └── ui/
        └── featurename/
            ├── FeatureNameRoute.kt  # uses hiltViewModel()
            ├── FeatureNameScreen.kt
            ├── FeatureNameViewModel.kt  # @HiltViewModel @Inject constructor
            └── FeatureNameUiState.kt
```

### `build.gradle.kts` (Tier 2 — Hilt + KSP, No Convention Plugins)

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.devtools.ksp")
    id("dagger.hilt.android.plugin")
}

android {
    namespace = "com.example.app"
    compileSdk = 36
    defaultConfig { minSdk = 26; targetSdk = 36 }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures { compose = true }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.hilt.android)
    ksp(libs.hilt.android.compiler)
    implementation(libs.androidx.hilt.navigation.compose)
    // Add Room only if persistence is needed:
    // implementation(libs.room.runtime)
    // implementation(libs.room.ktx)
    // ksp(libs.room.compiler)
    debugImplementation(libs.androidx.compose.ui.tooling)
}
```

No `build-logic/`, no multi-module. Repositories are interfaces bound in a single `AppModule.kt`. Use `hiltViewModel()` in Route composables and `@HiltViewModel @Inject constructor` on ViewModels — the same ViewModel/Repository/UiState code patterns as Tier 3, just in a flat module.

---

> **Tier 2 and Tier 3 only.** The sections below use Hilt and multi-layer architecture. For Tier 1, use the Simple Tier Patterns above.

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

> **Tier 3 only.** This multi-module layout does not apply to Tier 1 or Tier 2 projects.

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

> **Tier 3 only.** In Tier 1/2, add a new package under `app/src/main/.../ui/`.

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

> **Tier 2 and Tier 3** — requires Hilt. For Tier 1, use the companion object factory pattern above.

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

> **Tier 2 and Tier 3** — requires Hilt `@Inject constructor`. For Tier 1, use constructor injection via factory (no `@Inject` annotation needed).

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

> **Tier 3 only** — requires separate `api` and `impl` modules. Tier 2 uses `@Serializable` routes in a single module. Tier 1 uses string routes in a single `AppNavigation.kt` file.

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

> **Tier 2 and Tier 3 only.** Not used in Tier 1.

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

> **Tier 3 only.** Convention plugins and `build-logic/` are not used in Tier 1 or Tier 2. See the tier-specific `build.gradle.kts` examples in the Simple and Standard Tier Patterns sections above.

Use convention plugins in `build-logic/` for consistent configuration:
- `AndroidApplicationConventionPlugin` - App modules
- `AndroidLibraryConventionPlugin` - Library modules
- `AndroidFeatureConventionPlugin` - Feature modules
- `AndroidComposeConventionPlugin` - Compose setup (uses `kotlin-compose` plugin)
- `AndroidHiltConventionPlugin` - Hilt setup

**AGP 9.0 note**: Kotlin support is built into AGP 9.0 — remove `id("org.jetbrains.kotlin.android")` from plugin blocks.

See [gradle-setup.md](references/gradle-setup.md) for complete build configuration.
